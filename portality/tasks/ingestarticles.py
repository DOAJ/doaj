from portality import models, article
from portality.core import app

from portality.tasks.redis_huey import main_queue
from portality.decorators import write_required

from portality.background import BackgroundTask, BackgroundApi, BackgroundException
import ftplib, os, requests, traceback
from urlparse import urlparse

DEFAULT_MAX_REMOTE_SIZE=262144000
CHUNK_SIZE=1048576

def ftp_upload(path, parsed_url, file_upload):
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
            file_upload.failed("The file at the URL was too large")
            file_upload.save()
            print "...too large"
            return False


        f.close()
        f = ftplib.FTP(parsed_url.hostname, parsed_url.username, parsed_url.password)
        c = f.retrbinary('RETR ' + parsed_url.path, ftp_callback, CHUNK_SIZE)
        if too_large[0]:
            file_upload.failed("The file at the URL was too large")
            file_upload.save()
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


def http_upload(path, file_upload):
    try:
        r = requests.get(file_upload.filename, stream=True)

        # check the content length
        size_limit = app.config.get("MAX_REMOTE_SIZE", DEFAULT_MAX_REMOTE_SIZE)
        cl = r.headers.get("content-length")
        try:
            cl = int(cl)
        except:
            cl = 0
        if cl > size_limit:
            file_upload.failed("The file at the URL was too large")
            file_upload.save()
            print "...too large"
            return False

        too_large = False
        with open(path, 'wb') as f:
            downloaded = 0
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE): # 1Mb chunks
                downloaded += len(bytes(chunk))
                # check the size limit again
                if downloaded > size_limit:
                    file_upload.failed("The file at the URL was too large")
                    file_upload.save()
                    print "...too large"
                    too_large = True
                    break
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
    except:
        file_upload.failed("The URL could not be accessed")
        file_upload.save()
        print "...failed"
        return False

    if too_large:
        try:
            os.remove(path)
        except:
            pass
        return False

    return True

class IngestArticleBackgroundTask(BackgroundTask):

    __action__ = "ingest_article"

    def run(self):
        """
        Execute the task as specified by the background_jon
        :return:
        """
        job = self.background_job
        params = job.params

        file_upload_id = params.get("ingest_article__file_upload_id")
        if file_upload_id is None:
            raise BackgroundException(u"IngestArticleBackgroundTask.run run without sufficient parameters")

        file_upload = models.FileUpload.pull(file_upload_id)
        if file_upload is None:
            raise BackgroundException(u"IngestArticleBackgroundTask.run unable to find file upload with id {x}".format(x=file_upload_id))

        if file_upload.status == "exists":
            job.add_audit_message(u"Downloading file for file upload {x}, job {y}".format(x=file_upload_id, y=job.id))
            self._download(file_upload)
        elif file_upload.status == "validated":
            job.add_audit_message(u"Importing file for file upload {x}, job {y}".format(x=file_upload_id, y=job.id))
            self._process(file_upload)

    def _download(self, file_upload):
        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        remote_filename = file_upload.filename
        if isinstance(remote_filename, unicode):
            remote_filename = remote_filename.encode('utf-8', errors='ignore')
        # do not print the remote filename, can cause unicode errors,
        # and we've got the name in the "upload" type record in ES anyway!
        print 'processing upload record {0}'.format(file_upload.id)
        # first, determine if ftp or http
        parsed_url = urlparse(file_upload.filename)
        if parsed_url.scheme == 'ftp':
            if not ftp_upload(path, parsed_url, file_upload):
                return False
        elif parsed_url.scheme == 'http':
            if not http_upload(path, file_upload):
                return False
        else:
            print 'We only support HTTP and FTP uploads by URL. This is a: ' + parsed_url.scheme
            return False

        print "...downloaded as", file_upload.local_filename

        # now we have the record in the index and on disk, we can attempt to
        # validate it
        print "validating", file_upload.local_filename
        try:
            actual_schema = None
            with open(path) as handle:
                actual_schema = article.check_schema(handle, file_upload.schema)
        except:
            # file is a dud, so remove it
            try:
                os.remove(path)
            except:
                print traceback.format_exc()
            file_upload.failed("Unable to parse file")
            file_upload.save()
            print "...failed"
            return False

        # if we get to here then we have a successfully downloaded and validated
        # document, so we can write it to the index
        file_upload.validated(actual_schema)
        file_upload.save()
        print "...success"
        return True

    def _process(self, file_upload):
        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        print "importing ", path

        try:
            try:
                with open(path) as handle:
                    result = article.ingest_file(handle, format_name=file_upload.schema, owner=file_upload.owner, upload_id=file_upload.id)
                    success = result["success"]
                    fail = result["fail"]
                    update = result["update"]
                    new = result["new"]
            except article.IngestException as e:
                print "... ingest exception: ", e
                file_upload.failed(e.message)
                file_upload.save()
                try:
                    os.remove(path)
                except:
                    pass
            except Exception as e:
                print 'File system error while reading file'
                file_upload.failed("File system error when reading file")
                file_upload.save()
                try:
                    os.remove(path)
                except:
                    pass
            if success == 0 and fail > 0:
                file_upload.failed("All articles in file failed to import")
            if success > 0 and fail == 0:
                file_upload.processed(success, update, new)
            if success > 0 and fail > 0:
                file_upload.partial(success, fail, update, new)
            file_upload.save()
            print "... success"
            try:
                os.remove(path)
            except Exception as e:
                print u"Error while deleting file {0}: {1}".format(path, e.message)

        except Exception as e:
            print "... unexpected exception, " + e.message

    def cleanup(self):
        """
        Cleanup after a successful OR failed run of the task
        :return:
        """
        # remove the lock on the journal
        job = self.background_job
        params = job.params

    @classmethod
    def prepare(cls, username, **kwargs):
        """
        Take an arbitrary set of keyword arguments and return an instance of a BackgroundJob,
        or fail with a suitable exception

        :param kwargs: arbitrary keyword arguments pertaining to this task type
        :return: a BackgroundJob instance representing this task
        """

        upload_dir = app.config.get("UPLOAD_DIR")
        if upload_dir is None:
            raise BackgroundException("UPLOAD_DIR is not set in configuration")

        # first prepare a job record
        job = models.BackgroundJob()
        job.user = username
        job.action = cls.__action__

        file_upload_id = kwargs.get("file_upload_id")

        params ={}
        params["ingest_article__file_upload_id"] = file_upload_id

        if params["ingest_article__file_upload_id"] is None:
            raise BackgroundException(u"SetInDOAJBackgroundTask.prepare run without sufficient parameters")

        job.params = params
        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_job.save()
        ingest_article.schedule(args=(background_job.id,), delay=10)

@main_queue.task()
@write_required(script=True)
def ingest_article(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = IngestArticleBackgroundTask(job)
    BackgroundApi.execute(task)
