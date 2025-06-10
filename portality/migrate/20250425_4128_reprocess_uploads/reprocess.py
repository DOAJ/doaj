from portality.tasks.ingestarticles import IngestArticlesBackgroundTask, BackgroundException
from werkzeug.datastructures import FileStorage
from portality import models
from portality.core import app
import os
import time

incoming = models.FileUpload.by_properties("incoming")
for upload in incoming:
    if not (upload.schema is None or upload.schema == "doaj"):
        continue
    filepath = os.path.join(app.config.get("UPLOAD_DIR"), upload.local_filename)
    account = upload.owner
    previous = models.FileUpload.by_owner(account)
    try:
        with open(filepath, "rb") as f:
            upload_file = FileStorage(filename=upload.filename, stream=f)
            try:
                job = IngestArticlesBackgroundTask.prepare(account, upload_file=upload_file, schema="doaj", url=None, previous=previous)
                IngestArticlesBackgroundTask.submit(job)
            except BackgroundException as e:
                pass
    except FileNotFoundError as e:
        print("File not found: ", upload.local_filename, " for upload: ", upload.id)
        continue

    time.sleep(2)
    previous = models.FileUpload.by_owner(account)
    previous[0].set_created(upload.created_date)
    previous[0].save()

    print("Reprocessed upload: ", upload.id)
    upload.delete()

    print("Removing old upload: ", filepath)
    os.remove(filepath)
    