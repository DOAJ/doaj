from portality import models, article
from portality.core import app
import os

upload_dir = app.config.get("UPLOAD_DIR")
if upload_dir is None:
    print "UPLOAD_DIR is not set in configuration"
    exit()

to_process = models.FileUpload.list_valid() # returns an iterator
for upload in to_process:
    path = os.path.join(upload_dir, upload.local_filename)
    print "importing ", path
    
    try:
        with open(path) as handle:
            article.ingest_file(handle, upload.schema)
        upload.processed()
        upload.save()
        os.remove(path)
        print "... success"
    except article.IngestException as e:
        print "...", e
        upload.failed(e.message)
        upload.save()
        """
        try:
            os.remove(path)
        except:
            pass
        """
    except:
        print "... filesystem error"
        # there could be other sorts of errors, like filesystem ones
        upload.failed("File system error when reading file")
        upload.save()
        try:
            os.remove(path)
        except:
            pass
