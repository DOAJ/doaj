from doajtest.helpers import DoajTestCase
from doajtest.mocks.bll_article import BLLArticleMockFactory
from portality.constants import BgjobOutcomeStatus

from portality.tasks import ingestarticles
from doajtest.fixtures.article_crossref import Crossref531ArticleFixtureFactory
from doajtest.fixtures.accounts import AccountFixtureFactory
from doajtest.fixtures.article import ArticleFixtureFactory
from doajtest.mocks.file import FileMockFactory
from doajtest.mocks.response import ResponseMockFactory
from doajtest.mocks.ftp import FTPMockFactory
from doajtest.mocks.xwalk import XwalkMockFactory

from portality.bll.exceptions import IngestException

import time
from portality.crosswalks import article_crossref_xml
from portality.bll.services import article as articleSvc

from portality import models
from portality.core import app

from portality.background import BackgroundException, BackgroundTask

import ftplib, os, requests
from urllib.parse import urlparse
from lxml import etree

from portality.ui.messages import Messages

RESOURCES = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "unit", "resources")
ARTICLES = os.path.join(RESOURCES, "crossref531_article_uploads.xml")


def assert_outcome_fail_by_task(task: BackgroundTask):
    assert task.background_job.outcome_status == BgjobOutcomeStatus.Fail.value


class TestIngestArticlesCrossref531XML(DoajTestCase):

    @classmethod
    def setUpClass(self):
        super(TestIngestArticlesCrossref531XML, self).setUpClass()
        schema_path = app.config.get("SCHEMAS", {}).get("crossref531")
        schema_file = open(schema_path)
        schema_doc = etree.parse(schema_file)
        self.schema = etree.XMLSchema(schema_doc)

    def setUp(self):

        super(TestIngestArticlesCrossref531XML, self).setUp()
        self.cleanup_ids = []
        self.cleanup_paths = []

        self.schema_old = etree.XMLSchema

        self.xwalk_validate = article_crossref_xml.CrossrefXWalk531.validate
        self.batch_create_articles = articleSvc.ArticleService.batch_create_articles

        self.head = requests.head
        self.get = requests.get
        self.ftp = ftplib.FTP

        self.upload_dir = app.config["UPLOAD_DIR"]
        self.ingest_articles_retries = app.config['HUEY_TASKS']['ingest_articles']['retries']

    def tearDown(self):
        super(TestIngestArticlesCrossref531XML, self).tearDown()
        requests.head = self.head
        requests.get = self.get
        ftplib.FTP = self.ftp

        etree.XMLSchema = self.schema_old

        article_crossref_xml.CrossrefXWalk531.validate = self.xwalk_validate
        articleSvc.ArticleService.batch_create_articles = self.batch_create_articles

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

    def mock_load_schema(self, doc):
        return self.schema

    @classmethod
    def mock_unable_to_upload_schema(cls, doc):
        raise IngestException(u"Unable to load schema")

    def test_01_crossref_file_upload_success(self):

        etree.XMLSchema = self.mock_load_schema
        handle = Crossref531ArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)

        previous = []
        id = ingestarticles.IngestArticlesBackgroundTask._file_upload("testuser", f, "crossref531", previous)
        self.cleanup_ids.append(id)

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.schema == "crossref531"
        assert fu.status == "validated"

        path = os.path.join(app.config.get("UPLOAD_DIR", "."), id + ".xml")
        assert os.path.exists(path)

        assert len(previous) == 1

    def test_02_crossref_file_upload_invalid(self):

        etree.XMLSchema = self.mock_load_schema
        handle = Crossref531ArticleFixtureFactory.invalid_schema_xml()
        f = FileMockFactory(stream=handle)

        previous = []
        with self.assertRaises(BackgroundException):
            id = ingestarticles.IngestArticlesBackgroundTask._file_upload("testuser", f, "crossref531", previous)

        assert len(previous) == 1
        id = previous[0].id
        self.cleanup_ids.append(id)

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.status == "failed"
        assert fu.error is not None and fu.error != ""
        assert fu.error_details is not None and fu.error != ""
        assert list(fu.failure_reasons.keys()) == []

        # file should have been removed from upload dir
        path = os.path.join(app.config.get("UPLOAD_DIR", "."), id + ".xml")
        assert not os.path.exists(path)

        # and placed into the failed dir
        fad = os.path.join(app.config.get("FAILED_ARTICLE_DIR", "."), id + ".xml")
        assert os.path.exists(fad)

    def test_03_crossref_file_upload_fail(self):

        article_crossref_xml.CrossrefXWalk531.validate = XwalkMockFactory.validate
        etree.XMLSchema = self.mock_load_schema

        handle = Crossref531ArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)

        previous = []
        with self.assertRaises(BackgroundException):
            id = ingestarticles.IngestArticlesBackgroundTask._file_upload("testuser", f, "crossref531", previous)

        assert len(previous) == 1
        id = previous[0].id
        self.cleanup_ids.append(id)

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.status == "failed"
        assert fu.error is not None and fu.error != ""
        assert fu.error_details is None
        assert list(fu.failure_reasons.keys()) == []

        # file should have been removed from disk
        path = os.path.join(app.config.get("UPLOAD_DIR", "."), id + ".xml")
        assert not os.path.exists(path)

    def test_04_crossref_url_upload_http_success(self):

        # first try with a successful HEAD request
        requests.head = ResponseMockFactory.head_success
        requests.get = ResponseMockFactory.crossref531_get_success
        etree.XMLSchema = self.mock_load_schema

        url = "http://success"

        previous = []

        id = ingestarticles.IngestArticlesBackgroundTask._url_upload("testuser", url, "crossref531", previous)

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.schema == "crossref531"
        assert fu.status == "exists"

        assert len(previous) == 1

        # try that again, but with an unsuccessful HEAD request
        requests.head = ResponseMockFactory.head_fail

        previous = []

        id = ingestarticles.IngestArticlesBackgroundTask._url_upload("testuser", url, "crossref531", previous)

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.schema == "crossref531"
        assert fu.status == "exists"

        assert len(previous) == 1

    def test_05_crossref_url_upload_http_fail(self):

        # try with failing http requests
        requests.head = ResponseMockFactory.head_fail
        requests.get = ResponseMockFactory.get_fail
        etree.XMLSchema = self.mock_load_schema

        url = "http://fail"
        previous = []

        with self.assertRaises(BackgroundException):
            id = ingestarticles.IngestArticlesBackgroundTask._url_upload("testuser", url, "crossref531", previous)

        assert len(previous) == 1
        id = previous[0].id

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.status == "failed"
        assert fu.error is not None and fu.error != ""
        assert fu.error_details is None
        assert list(fu.failure_reasons.keys()) == []

        # now try again with an invalid url
        requests.head = ResponseMockFactory.head_success

        url = "other://url"
        previous = []

        with self.assertRaises(BackgroundException):
            id = ingestarticles.IngestArticlesBackgroundTask._url_upload("testuser", url, "crossref531", previous)

        assert len(previous) == 1
        id = previous[0].id

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.status == "failed"
        assert fu.error is not None and fu.error != ""
        assert fu.error_details is None
        assert list(fu.failure_reasons.keys()) == []

    def test_06_crossref_url_upload_ftp_success(self):

        ftplib.FTP = FTPMockFactory.create(schema="crossref531")
        previous = []
        url = "ftp://success"
        etree.XMLSchema = self.mock_load_schema

        id = ingestarticles.IngestArticlesBackgroundTask._url_upload("testuser", url, "crossref531", previous)

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.schema == "crossref531"
        assert fu.status == "exists"

        assert len(previous) == 1

    def test_07_url_upload_ftp_fail(self):

        ftplib.FTP = FTPMockFactory.create(schema="crossref531")
        previous = []
        url = "ftp://fail"
        with self.assertRaises(BackgroundException):
            id = ingestarticles.IngestArticlesBackgroundTask._url_upload("testuser", url, "crossref531", previous)

        assert len(previous) == 1
        id = previous[0].id

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.status == "failed"
        assert fu.error is not None and fu.error != ""
        assert fu.error_details is None
        assert list(fu.failure_reasons.keys()) == []

    def test_08_crossref_prepare_file_upload_success(self):

        handle = Crossref531ArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)
        etree.XMLSchema = self.mock_load_schema

        previous = []
        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testuser", upload_file=f, schema="crossref531",
                                                                  previous=previous)

        assert job is not None
        assert "ingest_articles__file_upload_id" in job.params
        id = job.params.get("ingest_articles__file_upload_id")
        self.cleanup_ids.append(id)

        assert len(previous) == 1

        fu = models.FileUpload.pull(id)
        assert fu is not None

    def test_09_prepare_file_upload_fail(self):

        article_crossref_xml.CrossrefXWalk531.validate = XwalkMockFactory.validate
        handle = Crossref531ArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)
        etree.XMLSchema = self.mock_load_schema

        previous = []
        with self.assertRaises(BackgroundException):
            job = ingestarticles.IngestArticlesBackgroundTask.prepare("testuser", upload_file=f, schema="crossref531",
                                                                      previous=previous)

        assert len(previous) == 1
        id = previous[0].id
        self.cleanup_ids.append(id)

        fu = models.FileUpload.pull(id)
        assert fu is not None

    def test_10_prepare_url_upload_success(self):

        requests.head = ResponseMockFactory.head_success
        url = "http://success"
        requests.get = ResponseMockFactory.crossref531_get_success
        etree.XMLSchema = self.mock_load_schema

        previous = []

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testuser", url=url, schema="crossref531",
                                                                  previous=previous)

        assert job is not None
        assert "ingest_articles__file_upload_id" in job.params
        id = job.params.get("ingest_articles__file_upload_id")
        self.cleanup_ids.append(id)

        assert len(previous) == 1

        fu = models.FileUpload.pull(id)
        assert fu is not None

    def test_11_prepare_url_upload_fail(self):

        # try with failing http requests
        requests.head = ResponseMockFactory.head_fail
        requests.get = ResponseMockFactory.get_fail
        url = "http://fail"
        previous = []
        etree.XMLSchema = self.mock_load_schema

        with self.assertRaises(BackgroundException):
            job = ingestarticles.IngestArticlesBackgroundTask.prepare("testuser", url=url, schema="crossref531",
                                                                      previous=previous)

        assert len(previous) == 1
        id = previous[0].id
        self.cleanup_ids.append(id)

        fu = models.FileUpload.pull(id)
        assert fu is not None

    def test_12_prepare_parameter_errors(self):

        etree.XMLSchema = self.mock_load_schema
        # no url or file upload
        with self.assertRaises(BackgroundException):
            job = ingestarticles.IngestArticlesBackgroundTask.prepare("testuser", schema="crossref531", previous=[])

        # no schema
        with self.assertRaises(BackgroundException):
            job = ingestarticles.IngestArticlesBackgroundTask.prepare("testuser", url="http://whatever", previous=[])

        # upload dir not configured
        del app.config["UPLOAD_DIR"]
        with self.assertRaises(BackgroundException):
            job = ingestarticles.IngestArticlesBackgroundTask.prepare("testuser", url="http://whatever", schema="doaj",
                                                                      previous=[])

    def test_13_ftp_upload_success(self):

        etree.XMLSchema = self.mock_load_schema
        ftplib.FTP = FTPMockFactory.create(schema="crossref531")

        file_upload = models.FileUpload()
        file_upload.set_id()

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)

        url = "ftp://upload"
        parsed_url = urlparse(url)

        job = models.BackgroundJob()

        result = ingestarticles.ftp_upload(job, path, parsed_url, file_upload)

        assert result is True
        assert os.path.exists(path)

        assert file_upload.status == "downloaded"

    def test_14_ftp_upload_fail(self):

        etree.XMLSchema = self.mock_load_schema
        ftplib.FTP = FTPMockFactory.create(schema="crossref531")

        file_upload = models.FileUpload()
        file_upload.set_id()

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)

        url = "ftp://fail"
        parsed_url = urlparse(url)

        job = models.BackgroundJob()

        result = ingestarticles.ftp_upload(job, path, parsed_url, file_upload)

        assert result is False
        assert file_upload.status == "failed"
        assert file_upload.error is not None and file_upload.error != ""
        assert file_upload.error_details is None
        assert list(file_upload.failure_reasons.keys()) == []

    def test_15_http_upload_success(self):

        etree.XMLSchema = self.mock_load_schema
        requests.head = ResponseMockFactory.head_fail
        requests.get = ResponseMockFactory.crossref531_get_success

        url = "http://upload"

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.upload("testuser", url, status="exists")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)

        job = models.BackgroundJob()

        result = ingestarticles.http_upload(job, path, file_upload)

        assert result is True
        assert os.path.exists(path)

        assert file_upload.status == "downloaded"

    def test_17_crossref_download_http_valid(self):

        etree.XMLSchema = self.mock_load_schema
        requests.head = ResponseMockFactory.head_fail
        requests.get = ResponseMockFactory.crossref531_get_success

        job = models.BackgroundJob()
        task = ingestarticles.IngestArticlesBackgroundTask(job)

        url = "http://valid"

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.upload("testuser", url, status="exists")
        file_upload.set_schema("crossref531")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)
        print(file_upload)

        result = task._download(file_upload)
        print(result)

        assert result is True
        assert file_upload.status == "validated"

    def test_18_download_http_invalid(self):

        etree.XMLSchema = self.mock_load_schema
        requests.head = ResponseMockFactory.head_fail
        requests.get = ResponseMockFactory.crossref531_get_success

        job = models.BackgroundJob()

        url = "http://upload"

        requests.get = ResponseMockFactory.crossref531_get_success

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.upload("testuser", url, status="exists")
        file_upload.set_schema("crossref531")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)
        self.cleanup_ids.append(file_upload.id)

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        result = task._download(file_upload)

        assert file_upload.status == "failed"
        assert file_upload.error is not None and file_upload.error != ""
        assert file_upload.error_details is not None and file_upload.error_details != ""
        assert list(file_upload.failure_reasons.keys()) == []

    def test_19_download_http_error(self):

        etree.XMLSchema = self.mock_load_schema
        requests.head = ResponseMockFactory.head_fail
        requests.get = ResponseMockFactory.get_fail

        job = models.BackgroundJob()

        url = "http://fail"

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.upload("testuser", url, status="exists")
        file_upload.set_schema("crossref531")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        result = task._download(file_upload)

        assert result is False
        assert file_upload.status == "failed"
        assert file_upload.error is not None and file_upload.error != ""
        assert file_upload.error_details is None
        assert list(file_upload.failure_reasons.keys()) == []

    def test_20_download_ftp_valid(self):

        etree.XMLSchema = self.mock_load_schema
        job = models.BackgroundJob()

        url = "ftp://valid"

        ftplib.FTP = FTPMockFactory.create(schema="crossref531")

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.upload("testuser", url, status="exists")
        file_upload.set_schema("crossref531")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        result = task._download(file_upload)

        assert result is True
        assert file_upload.status == "validated"

    def test_21_download_ftp_invalid(self):

        etree.XMLSchema = self.mock_load_schema
        job = models.BackgroundJob()

        url = "ftp://upload"

        ftplib.FTP = FTPMockFactory.create(schema="crossref531")

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.upload("testuser", url, status="exists")
        file_upload.set_schema("crossref531")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)
        self.cleanup_ids.append(file_upload.id)

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        result = task._download(file_upload)

        assert file_upload.status == "failed"
        assert file_upload.error is not None and file_upload.error != ""
        assert file_upload.error_details is not None and file_upload.error_details != ""
        assert list(file_upload.failure_reasons.keys()) == []

    def test_22_download_ftp_error(self):

        etree.XMLSchema = self.mock_load_schema
        job = models.BackgroundJob()

        url = "ftp://fail"
        ftplib.FTP = FTPMockFactory.create(schema="crossref531")

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.upload("testuser", url, status="exists")
        file_upload.set_schema("crossref531")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        result = task._download(file_upload)

        assert result is False
        assert file_upload.status == "failed"
        assert file_upload.error is not None and file_upload.error != ""
        assert file_upload.error_details is None
        assert list(file_upload.failure_reasons.keys()) == []

    def test_23_crossref_process_success(self):

        etree.XMLSchema = self.mock_load_schema
        j = models.Journal()
        j.set_in_doaj(True)
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save()

        # push an article to initialise the mappings
        source = ArticleFixtureFactory.make_article_source()
        article = models.Article(**source)
        article.save(blocking=True)
        article.delete()
        models.Article.blockdeleted(article.id)

        job = models.BackgroundJob()

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.set_schema("crossref531")
        file_upload.upload("testowner", "filename.xml")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)

        stream = Crossref531ArticleFixtureFactory.upload_1_issn_correct()
        with open(path, "wb") as f:
            f.write(stream.read())

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        task._process(file_upload)

        assert not os.path.exists(path)

        assert file_upload.status == "processed"
        assert file_upload.imported == 1
        assert file_upload.new == 1
        assert task.background_job.outcome_status == BgjobOutcomeStatus.Pending.value

    def test_24_process_invalid_file(self):

        etree.XMLSchema = self.mock_load_schema
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.save(blocking=True)

        job = models.BackgroundJob()
        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.set_schema("crossref531")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)
        self.cleanup_ids.append(file_upload.id)

        stream = Crossref531ArticleFixtureFactory.invalid_schema_xml()
        with open(path, "w") as f:
            f.write(stream.read())

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        task._process(file_upload)

        assert not os.path.exists(path)
        assert file_upload.status == "failed"
        assert file_upload.error is not None and file_upload.error != ""
        assert file_upload.error_details is not None and file_upload.error_details != ""
        assert list(file_upload.failure_reasons.keys()) == []
        assert_outcome_fail_by_task(task)

    def test_25_process_filesystem_error(self):

        etree.XMLSchema = self.mock_load_schema
        articleSvc.ArticleService.batch_create_articles = BLLArticleMockFactory.batch_create

        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.save(blocking=True)

        job = models.BackgroundJob()

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.set_schema("crossref531")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)
        self.cleanup_ids.append(file_upload.id)

        stream = Crossref531ArticleFixtureFactory.upload_1_issn_correct()
        with open(path, "wb") as f:
            f.write(stream.read())

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        task._process(file_upload)

        assert not os.path.exists(path)
        assert file_upload.status == "failed"
        assert file_upload.error is not None and file_upload.error != ""
        assert file_upload.error_details is None
        assert list(file_upload.failure_reasons.keys()) == []
        assert_outcome_fail_by_task(task)

    def test_26_run_validated(self):
        etree.XMLSchema = self.mock_load_schema
        j = models.Journal()
        j.set_in_doaj(True)
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save()

        # push an article to initialise the mappings
        source = ArticleFixtureFactory.make_article_source()
        article = models.Article(**source)
        article.save(blocking=True)
        article.delete()
        models.Article.blockdeleted(article.id)

        handle = Crossref531ArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)

        previous = []

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", upload_file=f, schema="crossref531",
                                                                  previous=previous)
        id = job.params.get("ingest_articles__file_upload_id")
        self.cleanup_ids.append(id)

        # because file upload gets created and saved by prepare
        time.sleep(2)

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        task.run()

        # because file upload needs to be re-saved
        time.sleep(2)

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.status == "processed"

    def test_27_run_exists(self):
        etree.XMLSchema = self.mock_load_schema
        requests.head = ResponseMockFactory.head_fail
        requests.get = ResponseMockFactory.crossref531_get_success

        j = models.Journal()
        j.set_in_doaj(True)
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save()

        # push an article to initialise the mappings
        source = ArticleFixtureFactory.make_article_source()
        article = models.Article(**source)
        article.save(blocking=True)
        article.delete()
        models.Article.blockdeleted(article.id)

        url = "http://valid"

        previous = []

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", url=url, schema="crossref531",
                                                                  previous=previous)
        id = job.params.get("ingest_articles__file_upload_id")
        self.cleanup_ids.append(id)

        # because file upload gets created and saved by prepare
        time.sleep(2)

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        task.run()

        # because file upload needs to be re-saved
        time.sleep(2)

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.status == "processed"
        assert job.outcome_status == BgjobOutcomeStatus.Pending

    def test_29_submit_success(self):
        etree.XMLSchema = self.mock_load_schema
        j = models.Journal()
        j.set_in_doaj(True)
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save()

        # push an article to initialise the mappings
        source = ArticleFixtureFactory.make_article_source()
        article = models.Article(**source)
        article.save(blocking=True)
        article.delete()
        models.Article.blockdeleted(article.id)

        handle = Crossref531ArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)

        previous = []

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", upload_file=f, schema="crossref531",
                                                                  previous=previous)
        id = job.params.get("ingest_articles__file_upload_id")
        self.cleanup_ids.append(id)

        # because file upload gets created and saved by prepare
        time.sleep(2)

        # scheduling does not result in immidiate execution for huey version > 2
        # always eager mode is replaced by immediate mode
        # in immediate mode scheduled jobs are not executed
        task = ingestarticles.IngestArticlesBackgroundTask(job)
        task.run()

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.status == "processed"

    def test_29_submit_multiple_affs(self):
        etree.XMLSchema = self.mock_load_schema
        j = models.Journal()
        j.set_in_doaj(True)
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save()

        # push an article to initialise the mappings
        source = ArticleFixtureFactory.make_article_source()
        article = models.Article(**source)
        article.save(blocking=True)
        article.delete()
        models.Article.blockdeleted(article.id)

        handle = Crossref531ArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="crossref531", upload_file=f)
        id = job.params.get("ingest_articles__file_upload_id")
        self.cleanup_ids.append(id)

        # because file upload gets created and saved by prepare
        time.sleep(2)

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        task.run()

        # because file upload needs to be re-saved
        time.sleep(2)

        found = [a for a in models.Article.find_by_issns(["1234-5678"])]
        assert len(found) == 1
        abib = found[0].bibjson()
        assert len(abib.author) == 2
        assert abib.author[0]["affiliation"] == "Cottage Labs University"

    def test_30_journal_not_indoaj(self):
        """ You can't upload an article for a journal that's been withdrawn"""
        etree.XMLSchema = self.mock_load_schema
        j = models.Journal()
        j.set_in_doaj(False)
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save()

        # push an article to initialise the mappings
        source = ArticleFixtureFactory.make_article_source()
        article = models.Article(**source)
        article.save(blocking=True)
        article.delete()
        models.Article.blockdeleted(article.id)

        job = models.BackgroundJob()

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.set_schema("crossref531")
        file_upload.upload("testowner", "filename.xml")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)

        stream = Crossref531ArticleFixtureFactory.upload_1_issn_correct()
        with open(path, "wb") as f:
            f.write(stream.read())

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        task._process(file_upload)

        assert not os.path.exists(path)

        assert file_upload.status == "failed"
        assert file_upload.error == Messages.EXCEPTION_ADDING_ARTICLE_TO_WITHDRAWN_JOURNAL
        assert_outcome_fail_by_task(task)
