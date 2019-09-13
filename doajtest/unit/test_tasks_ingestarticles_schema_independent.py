from doajtest.helpers import DoajTestCase

from portality.tasks import ingestarticles

from portality.bll.services import article as articleSvc

from portality import models
from portality.core import app

from portality.background import BackgroundException, RetryException

import ftplib, os, requests


DEFAULT_MAX_REMOTE_SIZE=262144000
CHUNK_SIZE=1048576

GET = requests.get

class MockResponse(object):
    def __init__(self, code, content=None):
        self.status_code = code
        self.headers = {"content-length" : 100}
        self.content = content

    def close(self):
        pass

    def iter_content(self, chunk_size=100):
        if self.content is None:
            for i in range(9):
                yield str(i) * chunk_size
        else:
            yield self.content

def mock_validate(handle, schema):
    raise RuntimeError("oops")

def mock_batch_create(*args, **kwargs):
    raise RuntimeError("oops")

def mock_head_success(url, *args, **kwargs):
    return MockResponse(200)

def mock_head_fail(url, *args, **kwargs):
    return MockResponse(405)

def mock_get_fail(url, *args, **kwargs):
    if url in ["http://fail"]:
        return MockResponse(405)
    if url in ["http://except"]:
        raise RuntimeError("oops")
    return GET(url, **kwargs)


class TestIngestArticles_SchemaIndependent(DoajTestCase):

    def setUp(self):
        super(TestIngestArticles_SchemaIndependent, self).setUp()

        self.cleanup_ids = []
        self.cleanup_paths = []

        self.batch_create_articles = articleSvc.ArticleService.batch_create_articles

        self.head = requests.head
        self.get = requests.get
        self.ftp = ftplib.FTP

        self.upload_dir = app.config["UPLOAD_DIR"]
        self.ingest_articles_retries = app.config['HUEY_TASKS']['ingest_articles']['retries']

    def tearDown(self):
        super(TestIngestArticles_SchemaIndependent, self).tearDown()

        articleSvc.ArticleService.batch_create_articles = self.batch_create_articles

        requests.head = self.head
        requests.get = self.get
        ftplib.FTP = self.ftp

        app.config["UPLOAD_DIR"] = self.upload_dir
        app.config["HUEY_TASKS"]["ingest_articles"]["retries"] = self.ingest_articles_retries

        for id in self.cleanup_ids:
            path = os.path.join(app.config.get("UPLOAD_DIR", "."), id + ".xml")
            if os.path.exists(path):
                os.remove(path)

        for id in self.cleanup_ids:
            path = os.path.join(app.config.get("FAILED_ARTICLE_DIR", "."), id + ".xml")
            if os.path.exists(path):
                os.remove(path)

        for path in self.cleanup_paths:
            if os.path.exists(path):
                os.remove(path)

    def test_16_http_upload_fail(self):
        requests.head = mock_head_fail
        requests.get = mock_get_fail

        url= "http://fail"

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.upload("testuser", url, status="exists")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)

        job = models.BackgroundJob()

        result = ingestarticles.http_upload(job, path, file_upload)

        assert result is False
        assert file_upload.status == "failed"
        assert file_upload.error is not None and file_upload.error != ""
        assert file_upload.error_details is None
        assert file_upload.failure_reasons.keys() == []

        # now try it with an actual exception
        url= "http://except"
        file_upload.upload("testuser", url, status="exists")

        result = ingestarticles.http_upload(job, path, file_upload)

        assert result is False
        assert file_upload.status == "failed"
        assert file_upload.error is not None and file_upload.error != ""
        assert file_upload.error_details is None
        assert file_upload.failure_reasons.keys() == []

    def test_28_run_errors(self):
        job = models.BackgroundJob()
        task = ingestarticles.IngestArticlesBackgroundTask(job)

        with self.assertRaises(BackgroundException):
            task.run()

        job.params = {}

        with self.assertRaises(BackgroundException):
            task.run()

        job.params = {"ingest_articles__file_upload_id": "whatever"}

        with self.assertRaises(BackgroundException):
            task.run()

    def test_30_submit_retry(self):
        app.config["HUEY_TASKS"]["ingest_articles"]["retries"] = 1

        fu = models.FileUpload()
        fu.validated("doaj")
        fu.save()

        job = models.BackgroundJob()
        params = {}
        params["ingest_articles__file_upload_id"] = fu.id
        params["ingest_articles__attempts"] = 0
        job.params = params
        job.save(blocking=True)

        # this assumes that huey is in always eager mode, and thus this immediately calls the async task,
        # which in turn calls execute, which ultimately calls run
        with self.assertRaises(RetryException):
            ingestarticles.IngestArticlesBackgroundTask.submit(job)

        job = models.BackgroundJob.pull(job.id)
        assert job.params.get("ingest_articles__attempts") == 1
        assert job.status == "processing"

        # now do it again, to see the retry cause the job to fail on the second attempt as per the config
        with self.assertRaises(RetryException):
            ingestarticles.IngestArticlesBackgroundTask.submit(job)

        job = models.BackgroundJob.pull(job.id)
        assert job.params.get("ingest_articles__attempts") == 2
        assert job.status == "error"