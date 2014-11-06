from portality import models, reapplication
from portality.core import app
import os

# first make sure we have enough information to run
upload_dir = app.config.get("REAPPLICATION_UPLOAD_DIR")
if upload_dir is None:
    print "REAPPLICATION_UPLOAD_DIR is not set in configuration"
    exit()

to_process = models.BulkUpload.list_incoming() # returns an iterator
for upload in to_process:
    # this will do most of the work - including changing the status of the upload
    reapplication.ingest_from_upload(upload)

    # if the ingest is successful then we can remove the CSV
    path = os.path.join(upload_dir, upload.local_filename)
    try:
        os.remove(path)
    except:
        pass