from portality import models, article
from portality.core import app
import os, requests, time

# first make sure we have enough information to run
upload_dir = app.config.get("UPLOAD_DIR")
if upload_dir is None:
    print "UPLOAD_DIR is not set in configuration"
    exit()

# our first task is to dereference and validate any remote files
to_download = models.FileUpload.list_remote()
for remote in to_download:
    path = os.path.join(upload_dir, remote.local_filename)
    print "downloading", remote.filename
    try:
        r = requests.get(remote.filename, stream=True)
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1048576): # 1Mb chunks
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
    except:
        remote.failed("The URL could not be accessed")
        remote.save()
        print "...failed"
        continue
    print "...downloaded as", remote.local_filename
    
    # now we have the record in the index and on disk, we can attempt to
    # validate it
    print "validating", remote.local_filename
    try:
        actual_schema = None
        with open(path) as handle:
            actual_schema = article.check_schema(handle, remote.schema)
    except:
        # file is a dud, so remove it
        try:
            os.remove(path)
        except:
            pass
        remote.failed("Unable to parse file")
        remote.save()
        print "...failed"
        continue
        
    # if we get to here then we have a successfully downloaded and validated
    # document, so we can write it to the index
    remote.validated(actual_schema)
    remote.save()
    print "...success"
    
# in between, issue a refresh request and wait for the index to sort itself out
models.FileUpload.refresh()
time.sleep(5)

to_process = models.FileUpload.list_valid() # returns an iterator
for upload in to_process:
    path = os.path.join(upload_dir, upload.local_filename)
    print "importing ", path
    
    try:
        with open(path) as handle:
            success, fail = article.ingest_file(handle, format_name=upload.schema, owner=upload.owner)
        if success == 0 and fail > 0:
            upload.failed("All articles in file failed to import")
        if success > 0 and fail == 0:
            upload.processed(success)
        if success > 0 and fail > 0:
            upload.partial(success, fail)
        upload.save()
        os.remove(path)
        print "... success"
    except article.IngestException as e:
        print "...", e
        upload.failed(e.message)
        upload.save()
        try:
            os.remove(path)
        except:
            pass
    except:
        print "... filesystem error"
        # there could be other sorts of errors, like filesystem ones
        upload.failed("File system error when reading file")
        upload.save()
        try:
            os.remove(path)
        except:
            pass
