from portality import models, article
from portality.core import app
import os, requests, time, ftplib
from urlparse import urlparse
import traceback

if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
    print "System is in READ-ONLY mode, script cannot run"
    exit()

DEFAULT_MAX_REMOTE_SIZE=262144000
CHUNK_SIZE=1048576

def ftp_upload():
    # 1. find out the file size
    #    (in the meantime the size command will return an error if
    #     the file does not exist)
    # 2. if not too big, download it
    size_limit = app.config.get("MAX_REMOTE_SIZE", DEFAULT_MAX_REMOTE_SIZE)

    too_large = [False]  # you CANNOT override (rebind) vars inside nested funcs in python 2
                         # and we can't pass too_large and downloaded as args to
                         # ftp_callback either since we don't control what args it gets
                         # hence, widely adopted ugly hack - since you can READ nonlocal
                         # vars from nested funcs, we use a mutable container!
    downloaded = [0]
    def ftp_callback(chunk):
        '''Callback for processing downloaded chunks of the FTP file'''
        if too_large[0]:
            return

        downloaded[0] += len(bytes(chunk))
        if downloaded[0] > size_limit:
            too_large[0] = True
            return

        if chunk:
            with open(path, 'ab') as o:
                o.write(chunk)
                o.flush()


    try:
        f = ftplib.FTP(parsed_url.hostname, parsed_url.username, parsed_url.password)
        r = f.sendcmd('TYPE I')  # SIZE is not usually allowed in ASCII mode, so set to binary mode
        if not r.startswith('2'):
            print '...could not set binary mode in target FTP server while checking file exists'
            return False
        file_size = f.size(parsed_url.path)
        if file_size < 0:
            # this will either raise an error which will get caught below
            # or, very rarely, will return an invalid size
            print '...invalid file size: ' + str(file_size)
            return False

        if file_size > size_limit:
            remote.failed("The file at the URL was too large")
            remote.save()
            print "...too large"
            return False


        f.close()
        f = ftplib.FTP(parsed_url.hostname, parsed_url.username, parsed_url.password)
        c = f.retrbinary('RETR ' + parsed_url.path, ftp_callback, CHUNK_SIZE)
        if too_large[0]:
            remote.failed("The file at the URL was too large")
            remote.save()
            print "...too large"
            try:
                os.remove(path)
            except:
                pass
            return False

        if c.startswith('226'):
            return True

        print 'Bad code returned by FTP server for the file transfer: "{0}"'.format(c)
        return False

    except Exception as e:
        print 'error during FTP file download: ' + str(e.args)
        return False


def http_upload():
    try:
        r = requests.get(remote.filename, stream=True)

        # check the content length
        size_limit = app.config.get("MAX_REMOTE_SIZE", DEFAULT_MAX_REMOTE_SIZE)
        cl = r.headers.get("content-length")
        try:
            cl = int(cl)
        except:
            cl = 0
        if cl > size_limit:
            remote.failed("The file at the URL was too large")
            remote.save()
            print "...too large"
            return False

        too_large = False
        with open(path, 'wb') as f:
            downloaded = 0
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE): # 1Mb chunks
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
    except:
        remote.failed("The URL could not be accessed")
        remote.save()
        print "...failed"
        return False

    if too_large:
        try:
            os.remove(path)
        except:
            pass
        return False

    return True

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
    remote_filename = remote.filename
    if isinstance(remote_filename, unicode):
        remote_filename = remote_filename.encode('utf-8', errors='ignore')
    # do not print the remote filename, can cause unicode errors,
    # and we've got the name in the "upload" type record in ES anyway!
    print 'processing upload record {0}'.format(remote.id)
    # first, determine if ftp or http
    parsed_url = urlparse(remote.filename)
    if parsed_url.scheme == 'ftp':
        if not ftp_upload():
            continue
    elif parsed_url.scheme == 'http':
        if not http_upload():
            continue
    else:
        print 'We only support HTTP and FTP uploads by URL. This is a: ' + parsed_url.scheme
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
            print traceback.format_exc()
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
