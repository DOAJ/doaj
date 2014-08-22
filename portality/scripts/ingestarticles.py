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
do_sleep = False
for remote in to_download:
    do_sleep = True
    path = os.path.join(upload_dir, remote.local_filename)
    print "downloading", remote.filename
    try:
        r = requests.get(remote.filename, stream=True)

        # check the content length
        size_limit = app.config.get("MAX_REMOTE_SIZE", 262144000)
        cl = r.headers.get("content-length")
        try:
            cl = int(cl)
        except:
            cl = 0
        if cl > size_limit:
            remote.failed("The file at the URL was too large")
            remote.save()
            print "...too large"
            continue
        
        too_large = False
        with open(path, 'wb') as f:
            downloaded = 0
            for chunk in r.iter_content(chunk_size=1048576): # 1Mb chunks
                downloaded += len(bytes(chunk))
                # check the size limit again
                if downloaded > size_limit:
                    remote.failed("The file at the URL was too large")
                    remote.save()
                    print "...too large"
                    too_large = True
                    break
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
        if too_large:
            try:
                os.remove(path)
            except:
                pass
            continue
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
if do_sleep:
    models.FileUpload.refresh()
    time.sleep(5)

to_process = models.FileUpload.list_valid() # returns an iterator
for upload in to_process:
    path = os.path.join(upload_dir, upload.local_filename)
    print "importing ", path
    
    try:
        with open(path) as handle:
            result = article.ingest_file(handle, format_name=upload.schema, owner=upload.owner, upload_id=upload.id)
            success = result["success"]
            fail = result["fail"]
            update = result["update"]
            new = result["new"]
        if success == 0 and fail > 0:
            upload.failed("All articles in file failed to import")
        if success > 0 and fail == 0:
            upload.processed(success, update, new)
        if success > 0 and fail > 0:
            upload.partial(success, fail, update, new)
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
    except Exception as e:
        # raise e
        print "... filesystem error"
        # there could be other sorts of errors, like filesystem ones
        upload.failed("File system error when reading file")
        upload.save()
        try:
            os.remove(path)
        except:
            pass
    
    # always refresh before moving on to the next file
    models.Article.refresh()
    time.sleep(5)
