import ftplib
import os
import requests
import time
from urllib.parse import urlparse

from lxml import etree

from doajtest import test_constants
from doajtest.fixtures import ArticleFixtureFactory, AccountFixtureFactory
from doajtest.fixtures.article_crossref import Crossref442ArticleFixtureFactory
from doajtest.helpers import DoajTestCase
from doajtest.mocks.bll_article import BLLArticleMockFactory
from doajtest.mocks.file import FileMockFactory
from doajtest.mocks.ftp import FTPMockFactory
from doajtest.mocks.response import ResponseMockFactory
from doajtest.mocks.xwalk import XwalkMockFactory
from portality import models
from portality.background import BackgroundException
from portality.bll.exceptions import IngestException
from portality.bll.services import article as articleSvc
from portality.core import app
from portality.crosswalks import article_crossref_xml
from portality.tasks import ingestarticles
from portality.ui.messages import Messages

ARTICLES = test_constants.PATH_RESOURCES / "crossref442_article_uploads.xml"

class TestIngestArticlesCrossref442XML(DoajTestCase):

    @classmethod
    def setUpClass(self):
        super(TestIngestArticlesCrossref442XML, self).setUpClass()
        schema_path = app.config.get("SCHEMAS", {}).get("crossref442")
        schema_file = open(schema_path)
        schema_doc = etree.parse(schema_file)
        self.schema = etree.XMLSchema(schema_doc)

    def setUp(self):

        super(TestIngestArticlesCrossref442XML, self).setUp()
        self.cleanup_ids = []
        self.cleanup_paths = []

        self.schema_old = etree.XMLSchema

        self.xwalk_validate = article_crossref_xml.CrossrefXWalk442.validate
        self.batch_create_articles = articleSvc.ArticleService.batch_create_articles

        self.head = requests.head
        self.get = requests.get
        self.ftp = ftplib.FTP

        self.upload_dir = app.config["UPLOAD_DIR"]
        self.ingest_articles_retries = app.config['HUEY_TASKS']['ingest_articles']['retries']

    def tearDown(self):
        super(TestIngestArticlesCrossref442XML, self).tearDown()
        requests.head = self.head
        requests.get = self.get
        ftplib.FTP = self.ftp

        etree.XMLSchema = self.schema_old

        article_crossref_xml.CrossrefXWalk442.validate = self.xwalk_validate
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
        handle = Crossref442ArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)

        previous = []
        id = ingestarticles.IngestArticlesBackgroundTask._file_upload("testuser", f, "crossref442", previous)
        self.cleanup_ids.append(id)

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.schema == "crossref442"
        assert fu.status == "validated"

        path = os.path.join(app.config.get("UPLOAD_DIR", "."), id + ".xml")
        assert os.path.exists(path)

        assert len(previous) == 1

    def test_02_crossref_file_upload_invalid(self):

        etree.XMLSchema = self.mock_load_schema
        handle = Crossref442ArticleFixtureFactory.invalid_schema_xml()
        f = FileMockFactory(stream=handle)

        previous = []
        with self.assertRaises(BackgroundException):
            id = ingestarticles.IngestArticlesBackgroundTask._file_upload("testuser", f, "crossref442", previous)

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

        article_crossref_xml.CrossrefXWalk442.validate = XwalkMockFactory.validate
        etree.XMLSchema = self.mock_load_schema

        handle = Crossref442ArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)

        previous = []
        with self.assertRaises(BackgroundException):
            id = ingestarticles.IngestArticlesBackgroundTask._file_upload("testuser", f, "crossref442", previous)

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
        requests.get = ResponseMockFactory.crossref442_get_success
        etree.XMLSchema = self.mock_load_schema

        url = "http://success"

        previous = []

        id = ingestarticles.IngestArticlesBackgroundTask._url_upload("testuser", url, "crossref442", previous)

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.schema == "crossref442"
        assert fu.status == "exists"

        assert len(previous) == 1

        # try that again, but with an unsuccessful HEAD request
        requests.head = ResponseMockFactory.head_fail

        previous = []

        id = ingestarticles.IngestArticlesBackgroundTask._url_upload("testuser", url, "crossref442", previous)

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.schema == "crossref442"
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
            id = ingestarticles.IngestArticlesBackgroundTask._url_upload("testuser", url, "crossref442", previous)

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
            id = ingestarticles.IngestArticlesBackgroundTask._url_upload("testuser", url, "crossref442", previous)

        assert len(previous) == 1
        id = previous[0].id

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.status == "failed"
        assert fu.error is not None and fu.error != ""
        assert fu.error_details is None
        assert list(fu.failure_reasons.keys()) == []

    def test_06_crossref_url_upload_ftp_success(self):

        ftplib.FTP = FTPMockFactory.create(schema="crossref442")
        previous = []
        url = "ftp://success"
        etree.XMLSchema = self.mock_load_schema

        id = ingestarticles.IngestArticlesBackgroundTask._url_upload("testuser", url, "crossref442", previous)

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.schema == "crossref442"
        assert fu.status == "exists"

        assert len(previous) == 1

    def test_07_url_upload_ftp_fail(self):

        ftplib.FTP = FTPMockFactory.create(schema="crossref442")
        previous = []
        url = "ftp://fail"
        with self.assertRaises(BackgroundException):
            id = ingestarticles.IngestArticlesBackgroundTask._url_upload("testuser", url, "crossref442", previous)

        assert len(previous) == 1
        id = previous[0].id

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.status == "failed"
        assert fu.error is not None and fu.error != ""
        assert fu.error_details is None
        assert list(fu.failure_reasons.keys()) == []

    def test_08_crossref_prepare_file_upload_success(self):

        handle = Crossref442ArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)
        etree.XMLSchema = self.mock_load_schema

        previous = []
        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testuser", upload_file=f, schema="crossref442",
                                                                  previous=previous)

        assert job is not None
        assert "ingest_articles__file_upload_id" in job.params
        id = job.params.get("ingest_articles__file_upload_id")
        self.cleanup_ids.append(id)

        assert len(previous) == 1

        fu = models.FileUpload.pull(id)
        assert fu is not None

    def test_09_prepare_file_upload_fail(self):

        article_crossref_xml.CrossrefXWalk442.validate = XwalkMockFactory.validate
        handle = Crossref442ArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)
        etree.XMLSchema = self.mock_load_schema

        previous = []
        with self.assertRaises(BackgroundException):
            job = ingestarticles.IngestArticlesBackgroundTask.prepare("testuser", upload_file=f, schema="crossref442",
                                                                      previous=previous)

        assert len(previous) == 1
        id = previous[0].id
        self.cleanup_ids.append(id)

        fu = models.FileUpload.pull(id)
        assert fu is not None

    def test_10_prepare_url_upload_success(self):

        requests.head = ResponseMockFactory.head_success
        url = "http://success"
        requests.get = ResponseMockFactory.crossref442_get_success
        etree.XMLSchema = self.mock_load_schema

        previous = []

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testuser", url=url, schema="crossref442", previous=previous)

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
            job = ingestarticles.IngestArticlesBackgroundTask.prepare("testuser", url=url, schema="crossref442",
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
            job = ingestarticles.IngestArticlesBackgroundTask.prepare("testuser", schema="crossref442", previous=[])

        # no schema
        with self.assertRaises(BackgroundException):
            job = ingestarticles.IngestArticlesBackgroundTask.prepare("testuser", url="http://whatever", previous=[])

        # upload dir not configured
        del app.config["UPLOAD_DIR"]
        with self.assertRaises(BackgroundException):
            job = ingestarticles.IngestArticlesBackgroundTask.prepare("testuser", url="http://whatever", schema="doaj", previous=[])

    def test_13_ftp_upload_success(self):

        etree.XMLSchema = self.mock_load_schema
        ftplib.FTP = FTPMockFactory.create(schema="crossref442")

        file_upload = models.FileUpload()
        file_upload.set_id()

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)

        url= "ftp://upload"
        parsed_url = urlparse(url)

        job = models.BackgroundJob()

        result = ingestarticles.ftp_upload(job, path, parsed_url, file_upload)

        assert result is True
        assert os.path.exists(path)

        assert file_upload.status == "downloaded"

    def test_14_ftp_upload_fail(self):

        etree.XMLSchema = self.mock_load_schema
        ftplib.FTP = FTPMockFactory.create(schema="crossref442")

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
        requests.get = ResponseMockFactory.crossref442_get_success

        url= "http://upload"

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
        requests.get = ResponseMockFactory.crossref442_get_success

        job = models.BackgroundJob()
        task = ingestarticles.IngestArticlesBackgroundTask(job)

        url = "http://valid"

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.upload("testuser", url, status="exists")
        file_upload.set_schema("crossref442")

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
        requests.get = ResponseMockFactory.crossref442_get_success

        job = models.BackgroundJob()

        url = "http://upload"

        requests.get = ResponseMockFactory.crossref442_get_success

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.upload("testuser", url, status="exists")
        file_upload.set_schema("crossref442")

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
        file_upload.set_schema("crossref442")

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

        ftplib.FTP = FTPMockFactory.create(schema="crossref442")

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.upload("testuser", url, status="exists")
        file_upload.set_schema("crossref442")

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

        ftplib.FTP = FTPMockFactory.create(schema="crossref442")

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.upload("testuser", url, status="exists")
        file_upload.set_schema("crossref442")

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
        ftplib.FTP = FTPMockFactory.create(schema="crossref442")

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.upload("testuser", url, status="exists")
        file_upload.set_schema("crossref442")

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
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.set_in_doaj(True)
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
        file_upload.set_schema("crossref442")
        file_upload.upload("testowner", "filename.xml")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)

        stream = Crossref442ArticleFixtureFactory.upload_1_issn_correct()
        with open(path, "wb") as f:
            f.write(stream.read())

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        task._process(file_upload)

        assert not os.path.exists(path)

        assert file_upload.status == "processed"
        assert file_upload.imported == 1
        assert file_upload.new == 1

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
        file_upload.set_schema("crossref442")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)
        self.cleanup_ids.append(file_upload.id)

        stream = Crossref442ArticleFixtureFactory.invalid_schema_xml()
        with open(path, "w") as f:
           f.write(stream.read())

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        task._process(file_upload)

        assert not os.path.exists(path)
        assert file_upload.status == "failed"
        assert file_upload.error is not None and file_upload.error != ""
        assert file_upload.error_details is not None and file_upload.error_details != ""
        assert list(file_upload.failure_reasons.keys()) == []

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
        file_upload.set_schema("crossref442")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)
        self.cleanup_ids.append(file_upload.id)

        stream = Crossref442ArticleFixtureFactory.upload_1_issn_correct()
        with open(path, "wb") as f:
            f.write(stream.read())

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        task._process(file_upload)

        assert not os.path.exists(path)
        assert file_upload.status == "failed"
        assert file_upload.error is not None and file_upload.error != ""
        assert file_upload.error_details is None
        assert list(file_upload.failure_reasons.keys()) == []

    def test_26_run_validated(self):
        etree.XMLSchema = self.mock_load_schema
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.set_in_doaj(True)
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

        handle = Crossref442ArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)

        previous = []

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", upload_file=f, schema="crossref442",
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
        requests.get = ResponseMockFactory.crossref442_get_success

        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.set_in_doaj(True)
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

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", url=url, schema="crossref442",
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

    def test_29_submit_success(self):
        etree.XMLSchema = self.mock_load_schema
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.set_in_doaj(True)
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

        handle = Crossref442ArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)

        previous = []

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", upload_file=f, schema="crossref442",
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

    def test_31_crossref_run_fail_unmatched_issn(self):
        etree.XMLSchema = self.mock_load_schema
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        bj.add_identifier(bj.E_ISSN, "9876-5432")
        j.set_in_doaj(True)
        j.save(blocking=True)

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save(blocking=True)

        handle = Crossref442ArticleFixtureFactory.upload_2_issns_ambiguous()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="crossref442", upload_file=f)
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
        assert fu.status == "failed"
        assert fu.error is not None and fu.error != ""
        assert fu.error_details is None

        fr = fu.failure_reasons
        assert "unmatched" in fr
        assert fr["unmatched"] == ["2345-6789"]

    def test_32_run_crossref_fail_shared_issn(self):
        etree.XMLSchema = self.mock_load_schema
        j1 = models.Journal()
        j1.set_owner("testowner1")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        bj1.add_identifier(bj1.E_ISSN, "9876-5432")
        j1.set_in_doaj(True)
        j1.save()

        j2 = models.Journal()
        j2.set_owner("testowner2")
        j2.set_in_doaj(True)
        bj2 = j2.bibjson()
        bj2.add_identifier(bj2.P_ISSN, "1234-5678")
        bj2.add_identifier(bj2.E_ISSN, "9876-5432")
        j2.save(blocking=True)

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner1")
        account.save(blocking=True)

        # crossref

        handle = Crossref442ArticleFixtureFactory.upload_2_issns_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner1", schema="crossref442", upload_file=f)
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
        assert fu.status == "failed"
        assert fu.error is not None and fu.error != ""
        assert fu.error_details is None

        fr = fu.failure_reasons
        assert "shared" in fr
        assert "1234-5678" in fr["shared"]
        assert "9876-5432" in fr["shared"]


    def test_33_run_fail_unowned_issn(self):
        # Create 2 journals with different owners and one different issn each.  The two issns in the
        # article match each of the journals respectively
        # We expect an ingest failure
        etree.XMLSchema = self.mock_load_schema
        j1 = models.Journal()
        j1.set_owner("testowner1")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        j1.set_in_doaj(True)
        j1.save()

        j2 = models.Journal()
        j2.set_owner("testowner2")
        j2.set_in_doaj(True)
        bj2 = j2.bibjson()
        bj2.add_identifier(bj2.E_ISSN, "9876-5432")
        j2.save(blocking=True)

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save(blocking=True)

        handle = Crossref442ArticleFixtureFactory.upload_2_issns_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="crossref442", upload_file=f)
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
        assert fu.status == "failed"
        assert fu.error is not None and fu.error != ""
        assert fu.error_details is None

        fr = fu.failure_reasons
        assert "unowned" in fr
        assert "9876-5432" in fr["unowned"]

    def test_34_crossref_journal_2_article_2_success(self):
        etree.XMLSchema = self.mock_load_schema
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        bj.add_identifier(bj.E_ISSN, "9876-5432")
        j.set_in_doaj(True)
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

        handle = Crossref442ArticleFixtureFactory.upload_2_issns_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="crossref442", upload_file=f)
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
        assert fu.imported == 1
        assert fu.updates == 0
        assert fu.new == 1

        fr = fu.failure_reasons
        assert len(fr.get("shared", [])) == 0
        assert len(fr.get("unowned", [])) == 0
        assert len(fr.get("unmatched", [])) == 0

        found = [a for a in models.Article.find_by_issns(["1234-5678", "9876-5432"])]
        assert len(found) == 1


    def test_35_crossref_journal_2_article_1_success(self):
        etree.XMLSchema = self.mock_load_schema
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        bj.add_identifier(bj.E_ISSN, "9876-5432")
        j.set_in_doaj(True)
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

        handle = Crossref442ArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="crossref442", upload_file=f)
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
        assert fu.imported == 1
        assert fu.updates == 0
        assert fu.new == 1

        fr = fu.failure_reasons
        assert len(fr.get("shared", [])) == 0
        assert len(fr.get("unowned", [])) == 0
        assert len(fr.get("unmatched", [])) == 0

        found = [a for a in models.Article.find_by_issns(["1234-5678"])]
        assert len(found) == 1

    def test_37_crossref_journal_1_article_1_success(self):
        etree.XMLSchema = self.mock_load_schema
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.set_in_doaj(True)
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

        handle = Crossref442ArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="crossref442", upload_file=f)
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
        assert fu.imported == 1
        assert fu.updates == 0
        assert fu.new == 1

        fr = fu.failure_reasons
        assert len(fr.get("shared", [])) == 0
        assert len(fr.get("unowned", [])) == 0
        assert len(fr.get("unmatched", [])) == 0

        found = [a for a in models.Article.find_by_issns(["1234-5678"])]
        assert len(found) == 1

    def test_38_crossref_journal_2_article_2_1_different_success(self):
        etree.XMLSchema = self.mock_load_schema
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        bj.add_identifier(bj.E_ISSN, "9876-5432")
        j.set_in_doaj(True)
        j.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save(blocking=True)

        handle = Crossref442ArticleFixtureFactory.upload_2_issns_ambiguous()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="crossref442", upload_file=f)
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
        assert fu.status == "failed"
        assert fu.imported == 0
        assert fu.updates == 0
        assert fu.new == 0

        fr = fu.failure_reasons
        assert len(fr.get("shared", [])) == 0
        assert len(fr.get("unowned", [])) == 0
        assert len(fr.get("unmatched", [])) == 1

        found = [a for a in models.Article.find_by_issns(["1234-5678", "2345-6789"])]
        assert len(found) == 0

    def test_39_crossref_2_journals_different_owners_both_issns_fail(self):
        etree.XMLSchema = self.mock_load_schema
        j1 = models.Journal()
        j1.set_owner("testowner1")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        bj1.add_identifier(bj1.E_ISSN, "9876-5432")
        j1.set_in_doaj(True)
        j1.save()

        j2 = models.Journal()
        j2.set_owner("testowner2")
        j2.set_in_doaj(True)
        bj2 = j2.bibjson()
        bj2.add_identifier(bj2.P_ISSN, "1234-5678")
        bj2.add_identifier(bj2.E_ISSN, "9876-5432")
        j2.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner1")
        account.save(blocking=True)

        handle = Crossref442ArticleFixtureFactory.upload_2_issns_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner1", schema="crossref442", upload_file=f)
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
        assert fu.status == "failed"
        assert fu.imported == 0
        assert fu.updates == 0
        assert fu.new == 0

        fr = fu.failure_reasons
        assert len(fr.get("shared", [])) == 2
        assert "1234-5678" in fr["shared"]
        assert "9876-5432" in fr["shared"]
        assert len(fr.get("unowned", [])) == 0
        assert len(fr.get("unmatched", [])) == 0

        found = [a for a in models.Article.find_by_issns(["1234-5678", "9876-5432"])]
        assert len(found) == 0

    def test_40_crossref_2_journals_different_owners_issn_each_fail(self):
        etree.XMLSchema = self.mock_load_schema
        # Create 2 journals with different owners and one different issn each.  The two issns in the
        # article match each of the journals respectively
        # We expect an ingest failure
        j1 = models.Journal()
        j1.set_owner("testowner1")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        j1.set_in_doaj(True)
        j1.save()

        j2 = models.Journal()
        j2.set_owner("testowner2")
        j2.set_in_doaj(True)
        bj2 = j2.bibjson()
        bj2.add_identifier(bj2.E_ISSN, "9876-5432")
        j2.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner1")
        account.save(blocking=True)

        handle = Crossref442ArticleFixtureFactory.upload_2_issns_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner1", schema="crossref442", upload_file=f)
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
        assert fu.status == "failed"
        assert fu.imported == 0
        assert fu.updates == 0
        assert fu.new == 0

        fr = fu.failure_reasons
        assert len(fr.get("shared", [])) == 0
        assert len(fr.get("unowned", [])) == 1
        assert "9876-5432" in fr["unowned"]
        assert len(fr.get("unmatched", [])) == 0

        found = [a for a in models.Article.find_by_issns(["1234-5678", "9876-5432"])]
        assert len(found) == 0

    def test_41_crossref_2_journals_same_owner_issn_each_success(self):
        etree.XMLSchema = self.mock_load_schema
        # Create 2 journals with the same owner, each with one different issn.  The article's 2 issns
        # match each of these issns
        # We expect a successful article ingest

        j1 = models.Journal()
        j1.set_owner("testowner")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        j1.set_in_doaj(True)
        j1.save()

        j2 = models.Journal()
        j2.set_owner("testowner")
        j2.set_in_doaj(True)
        bj2 = j2.bibjson()
        bj2.add_identifier(bj2.E_ISSN, "9876-5432")
        j2.save()

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

        handle = Crossref442ArticleFixtureFactory.upload_2_issns_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="crossref442", upload_file=f)
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
        assert fu.imported == 1
        assert fu.updates == 0
        assert fu.new == 1

        fr = fu.failure_reasons
        assert len(fr.get("shared", [])) == 0
        assert len(fr.get("unowned", [])) == 0
        assert len(fr.get("unmatched", [])) == 0

        found = [a for a in models.Article.find_by_issns(["1234-5678", "9876-5432"])]
        assert len(found) == 1


    def test_42_crossref_2_journals_different_owners_different_issns_mixed_article_fail(self):
        etree.XMLSchema = self.mock_load_schema
        # Create 2 different journals with different owners and different issns (2 each).
        # The article's issns match one issn in each journal
        # We expect an ingest failure
        j1 = models.Journal()
        j1.set_owner("testowner1")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        bj1.add_identifier(bj1.E_ISSN, "2345-6789")
        j1.set_in_doaj(True)
        j1.save()

        j2 = models.Journal()
        j2.set_owner("testowner2")
        j2.set_in_doaj(True)
        bj2 = j2.bibjson()
        bj2.add_identifier(bj2.P_ISSN, "8765-4321")
        bj2.add_identifier(bj2.E_ISSN, "9876-5432")
        j2.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner1")
        account.save(blocking=True)

        handle = Crossref442ArticleFixtureFactory.upload_2_issns_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner1", schema="crossref442", upload_file=f)
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
        assert fu.status == "failed"
        assert fu.imported == 0
        assert fu.updates == 0
        assert fu.new == 0

        fr = fu.failure_reasons
        assert len(fr.get("shared", [])) == 0
        assert len(fr.get("unowned", [])) == 1
        assert "9876-5432" in fr["unowned"]
        assert len(fr.get("unmatched", [])) == 0

        found = [a for a in models.Article.find_by_issns(["1234-5678", "9876-5432"])]
        assert len(found) == 0

    def test_43_duplication(self):
        etree.XMLSchema = self.mock_load_schema
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        bj.add_identifier(bj.E_ISSN, "9876-5432")
        j.set_in_doaj(True)
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

        # make both handles, as we want as little gap as possible between requests in a moment
        handle1 = Crossref442ArticleFixtureFactory.upload_2_issns_correct()
        handle2 = Crossref442ArticleFixtureFactory.upload_2_issns_correct()

        f1 = FileMockFactory(stream=handle1)
        f2 = FileMockFactory(stream=handle2)

        job1 = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="crossref442", upload_file=f1)
        id1 = job1.params.get("ingest_articles__file_upload_id")
        self.cleanup_ids.append(id1)

        job2 = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="crossref442", upload_file=f2)
        id2 = job2.params.get("ingest_articles__file_upload_id")
        self.cleanup_ids.append(id2)

        # because file upload gets created and saved by prepare
        time.sleep(2)

        task1 = ingestarticles.IngestArticlesBackgroundTask(job1)
        task2 = ingestarticles.IngestArticlesBackgroundTask(job2)

        task1.run()
        task2.run()

        # because file upload needs to be re-saved
        time.sleep(2)

        fu1 = models.FileUpload.pull(id1)
        fu2 = models.FileUpload.pull(id2)

        assert fu1.status == "processed"
        assert fu2.status == "processed"

        # now let's check that only one article got created
        found = [a for a in models.Article.find_by_issns(["1234-5678", "9876-5432"])]
        assert len(found) == 1, "found: {}".format(len(found))

    def test_44_journal_1_article_1_superlong_noclip(self):
        etree.XMLSchema = self.mock_load_schema
        # Create a journal with 1 issn, which is the same 1 issn on the article
        # we expect a successful article ingest
        # But it's just shy of 30000 unicode characters long!

        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.set_in_doaj(True)
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

        handle = Crossref442ArticleFixtureFactory.upload_1_issn_superlong_should_not_clip()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="crossref442", upload_file=f)
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
        assert fu.imported == 1
        assert fu.updates == 0
        assert fu.new == 1

        fr = fu.failure_reasons
        assert len(fr.get("shared", [])) == 0
        assert len(fr.get("unowned", [])) == 0
        assert len(fr.get("unmatched", [])) == 0

        found = [a for a in models.Article.find_by_issns(["1234-5678"])]
        assert len(found) == 1
        assert len(found[0].bibjson().abstract) == 26328

    def test_45_crossref_journal_1_article_1_superlong_clip(self):
        etree.XMLSchema = self.mock_load_schema
        # Create a journal with 1 issn, which is the same 1 issn on the article
        # we expect a successful article ingest
        # But it's over 40k unicode characters long!

        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.set_in_doaj(True)
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

        handle = Crossref442ArticleFixtureFactory.upload_1_issn_superlong_should_clip()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="crossref442", upload_file=f)
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
        assert fu.imported == 1
        assert fu.updates == 0
        assert fu.new == 1

        fr = fu.failure_reasons
        assert len(fr.get("shared", [])) == 0
        assert len(fr.get("unowned", [])) == 0
        assert len(fr.get("unmatched", [])) == 0

        found = [a for a in models.Article.find_by_issns(["1234-5678"])]
        assert len(found) == 1
        assert len(found[0].bibjson().abstract) == 30000

    def test_46_one_journal_one_article_2_issns_one_unknown(self):
        etree.XMLSchema = self.mock_load_schema
        # Create one journal and ingest one article.  The Journal has two issns, and the article
        # has two issns, but one of the journal's issns is unknown
        # We expect an ingest failure

        j1 = models.Journal()
        j1.set_owner("testowner1")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        bj1.add_identifier(bj1.E_ISSN, "2222-2222")
        j1.set_in_doaj(True)
        j1.save(blocking=True)

        saved = models.Journal.find_by_issn("1234-5678")

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner1")
        account.save(blocking=True)

        handle = Crossref442ArticleFixtureFactory.upload_2_issns_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner1", schema="crossref442", upload_file=f)
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
        assert fu.status == "failed"
        assert fu.imported == 0
        assert fu.updates == 0
        assert fu.new == 0

        fr = fu.failure_reasons
        assert len(fr.get("shared", [])) == 0
        assert len(fr.get("unowned", [])) == 0
        assert len(fr.get("unmatched", [])) == 1, "expected len = 1, received: {}".format(fr.get("unmatched"))
        assert "9876-5432" in fr["unmatched"]

        found = [a for a in models.Article.find_by_issns(["1234-5678", "9876-5432"])]
        assert len(found) == 0

    def test_47_crossref_lcc_spelling_error(self):
        etree.XMLSchema = self.mock_load_schema
        # create a journal with a broken subject classification
        j1 = models.Journal()
        j1.set_owner("testowner1")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        bj1.add_identifier(bj1.E_ISSN, "9876-5432")
        bj1.add_subject("LCC", "Whatever", "WHATEVA")
        bj1.add_subject("LCC", "Aquaculture. Fisheries. Angling", "SH1-691")
        j1.set_in_doaj(True)
        j1.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner1")
        account.save()

        # push an article to initialise the mappings
        source = ArticleFixtureFactory.make_article_source()
        article = models.Article(**source)
        article.save(blocking=True)
        article.delete()
        models.Article.blockdeleted(article.id)

        handle = Crossref442ArticleFixtureFactory.upload_2_issns_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner1", schema="crossref442", upload_file=f)
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
        assert fu.status == "processed", "expected processed, received: {}".format(fu.status)
        assert fu.imported == 1
        assert fu.updates == 0
        assert fu.new == 1

        fr = fu.failure_reasons
        assert len(fr.get("shared", [])) == 0
        assert len(fr.get("unowned", [])) == 0
        assert len(fr.get("unmatched", [])) == 0

        found = [a for a in models.Article.find_by_issns(["1234-5678", "9876-5432"])]
        assert len(found) == 1

        cpaths = found[0].data["index"]["classification_paths"]
        assert len(cpaths) == 1
        assert cpaths[0] == "Agriculture: Aquaculture. Fisheries. Angling"

    def test_48_crossref_unknown_journal_issn(self):
        etree.XMLSchema = self.mock_load_schema
        # create a journal with one of the ISSNs specified
        j1 = models.Journal()
        j1.set_owner("testowner1")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        j1.set_in_doaj(True)
        j1.save(blocking=True)

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner1")
        account.save(blocking=True)

        # take an article with 2 issns, but one of which is not in the index
        handle = Crossref442ArticleFixtureFactory.upload_2_issns_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner1", schema="crossref442", upload_file=f)
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
        assert fu.status == "failed"
        assert fu.imported == 0
        assert fu.updates == 0
        assert fu.new == 0

        fr = fu.failure_reasons
        assert len(fr.get("shared", [])) == 0
        assert len(fr.get("unowned", [])) == 0
        assert len(fr.get("unmatched", [])) == 1

    def test_49_crossref_noids(self):
        etree.XMLSchema = self.mock_load_schema
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.save(blocking=True)

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save(blocking=True)

        job = models.BackgroundJob()

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.set_schema("crossref442")
        file_upload.upload("testowner", "filename.xml")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)

        stream = Crossref442ArticleFixtureFactory.noids()
        with open(path, "wb") as f:
            f.write(stream.read())

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        task._process(file_upload)

        assert not os.path.exists(path)

        assert file_upload.status == "failed"

    def test_49_1_determine_issns_types(self):
        etree.XMLSchema = self.mock_load_schema
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        bj.add_identifier(bj.E_ISSN, "9876-5432")
        j.set_in_doaj(True)
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
        file_upload.set_schema("crossref442")
        file_upload.upload("testowner", "filename.xml")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)

        fixtureFactoryMethods = [Crossref442ArticleFixtureFactory.upload_1_issn_electronic,
                                Crossref442ArticleFixtureFactory.upload_1_issn_print,
                                Crossref442ArticleFixtureFactory.upload_1_issn_no_type,

                                Crossref442ArticleFixtureFactory.upload_2_issns_1_electronic_2_no_type,
                                Crossref442ArticleFixtureFactory.upload_2_issns_1_electronic_2_print,
                                Crossref442ArticleFixtureFactory.upload_2_issns_1_no_type_2_electronic,
                                Crossref442ArticleFixtureFactory.upload_2_issns_1_print_2_no_type,
                                Crossref442ArticleFixtureFactory.upload_2_issns_1_print_2_electronic,
                                Crossref442ArticleFixtureFactory.upload_2_issns_1_no_type_2_print,
                                Crossref442ArticleFixtureFactory.upload_2_issns_no_type]

        # fixtureFactoryMethods = [Crossref442ArticleFixtureFactory.upload_1_issn_print]

        for m in fixtureFactoryMethods:
            handle = m()

            f = FileMockFactory(stream=handle)

            job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="crossref442", upload_file=f)
            id = job.params.get("ingest_articles__file_upload_id")
            self.cleanup_ids.append(id)
            models.FileUpload.block(id)
            # because file upload gets created and saved by prepare
            # time.sleep(2)

            task = ingestarticles.IngestArticlesBackgroundTask(job)
            task.run()

            # because file upload needs to be re-saved
            # time.sleep(2)

            fu = models.FileUpload.pull(id)

            assert fu.status == "processed", "expected 'processed', received: {}, , error code: {}, for: {}".format(file_upload.status, file_upload.error, m)

        # because file upload needs to be re-saved
        time.sleep(2)

        found = [a for a in models.Article.find_by_issns(["9876-5432", "1234-5678"])]

        assert len(fixtureFactoryMethods) == len(found), "expected: {}, found: {}".format(len(fixtureFactoryMethods), [a.bibjson().title for a in found])
        for a in found:
            bib = a.bibjson()
            if bib.title == "1 ISSN - electronic" or bib.title == "1 ISSN - no type":
                assert bib.get_one_identifier(bib.E_ISSN) == "9876-5432", "article '{}' expects to have EISSN: 9876-5432".format(bib.title)
                assert bib.get_one_identifier(bib.P_ISSN) is None, "article '{}' should not have PISSN".format(bib.title)
            elif bib.title == "1 ISSN - print":
                assert bib.get_one_identifier(
                    bib.P_ISSN) == "1234-5678", "article '{}' expects to have PISSN: 1234-5678".format(bib.title)
                assert bib.get_one_identifier(bib.E_ISSN) is None, "article '{}' should not have EISSN".format(
                    bib.title)
            else:
                assert bib.get_one_identifier(
                    bib.P_ISSN) == "1234-5678", "article '{}' expects to have PISSN: 1234-5678".format(bib.title)
                assert bib.get_one_identifier(bib.E_ISSN) == "9876-5432", "article '{}' expects to have EISSN: 9876-5432".format(bib.title)


    def test_49_2_issns_same_type(self):
        etree.XMLSchema = self.mock_load_schema
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        bj.add_identifier(bj.E_ISSN, "9876-5432")
        j.save(blocking=True)

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save(blocking=True)

        job = models.BackgroundJob()

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.set_schema("crossref442")
        file_upload.upload("testowner", "filename.xml")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)

        stream = Crossref442ArticleFixtureFactory.upload_2_issns_same_types()
        with open(path, "wb") as f:
            f.write(stream.read())

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        task._process(file_upload)

        assert not os.path.exists(path)

        assert file_upload.status == "failed", "expected 'failed', received: {}".format(file_upload.status)
        assert file_upload.error == "Both ISSNs have the same type: print", "expected error: 'Both ISSNs have the same type: print', received: {}".format(file_upload.error)

    def test_50_3_issns(self):
        etree.XMLSchema = self.mock_load_schema
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        bj.add_identifier(bj.E_ISSN, "9876-5432")
        j.save(blocking=True)

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save(blocking=True)

        job = models.BackgroundJob()

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.set_schema("crossref442")
        file_upload.upload("testowner", "filename.xml")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)

        stream = Crossref442ArticleFixtureFactory.upload_3_issns()
        with open(path, "wb") as f:
            f.write(stream.read())

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        task._process(file_upload)

        assert not os.path.exists(path)

        assert file_upload.status == "failed", "expected 'failed', received: {}".format(file_upload.status)
        assert file_upload.error == Messages.EXCEPTION_TOO_MANY_ISSNS, "expected error: {}, received: {}".format(Messages.EXCEPTION_TOO_MANY_ISSNS,
            file_upload.error)

    def test_51_same_issns(self):
        etree.XMLSchema = self.mock_load_schema
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        bj.add_identifier(bj.E_ISSN, "9876-5432")
        j.save(blocking=True)

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save(blocking=True)

        job = models.BackgroundJob()

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.set_schema("crossref442")
        file_upload.upload("testowner", "filename.xml")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)

        stream = Crossref442ArticleFixtureFactory.upload_the_same_issns()
        with open(path, "wb") as f:
            f.write(stream.read())

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        task._process(file_upload)

        assert not os.path.exists(path)

        assert file_upload.status == "failed", "expected 'failed', received: {}".format(file_upload.status)
        assert file_upload.error == Messages.EXCEPTION_IDENTICAL_PISSN_AND_EISSN, "expected error: {}, received: {}".format(Messages.EXCEPTION_IDENTICAL_PISSN_AND_EISSN,
            file_upload.error)

    def test_52_html_tags_in_title_text(self):
        NS = {'x': 'http://www.crossref.org/schema/4.4.2'}

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save()

        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        bj.add_identifier(bj.E_ISSN, "9876-5432")
        j.set_in_doaj(True)
        j.save()

        # push an article to initialise the mappings
        source = ArticleFixtureFactory.make_article_source()
        article = models.Article(**source)
        article.save(blocking=True)
        article.delete()
        models.Article.blockdeleted(article.id)

        etree.XMLSchema = self.mock_load_schema

        xpath = "//x:body/x:journal[x:journal_metadata[x:full_title='HTML tags in title']]"

        with open(ARTICLES, "r") as f:
            data = f.read()
        new_data = data.replace("{REPLACEME}", "This article has <i>unescaped</i> and &lt;i&gt;escaped&lt;/i&gt; html tags")
        with open(ARTICLES, "w") as f:
            f.write(new_data)

        stream = Crossref442ArticleFixtureFactory.upload_html_tags_in_text()
        f = FileMockFactory(stream=stream)

        previous = []
        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="crossref442", upload_file=f)
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
        assert fu.status == "processed", "fu.status expected processed, received: {}".format(fu.status)

        # because file upload needs to be re-saved
        time.sleep(2)

        found = [a for a in models.Article.find_by_issns(["9876-5432", "1234-5678"])]

        assert len(found) == 1, "expected 1, found: {}".format(len(found))
        art = found[0]
        bib = art.bibjson()
        assert bib.title == "This article has <ns0:i>unescaped</ns0:i> and &lt;i&gt;escaped&lt;/i&gt; html tags", "expected: 'This article has <i>unescaped</i> and &lt;i&gt;unexcaped&lt;/i&gt; html tags', received: {}".format(bib.title)

        with open(ARTICLES, "r") as f:
            data = f.read()
        new_data = data.replace("This article has <i>unescaped</i> and &lt;i&gt;escaped&lt;/i&gt; html tags", "{REPLACEME}")
        with open(ARTICLES, "w") as f:
            f.write(new_data)

    def test_53_html_tags_in_title_attr(self):
        file = etree.parse(ARTICLES)
        root = file.getroot()
        NS = {'x': 'http://www.crossref.org/schema/4.4.2'}
        issn = root.xpath("//x:body/x:journal[x:journal_metadata[x:full_title='HTML tags in attribute']]/x:journal_metadata/x:issn", namespaces=NS)[0]
        old_attr = issn.attrib["media_type"]
        issn.attrib["media_type"] = "Here is some attribute <i>with unescaped tags </i> in it"

        etree.ElementTree(root).write(ARTICLES, pretty_print=True)

        etree.XMLSchema = self.mock_load_schema
        handle = Crossref442ArticleFixtureFactory.upload_html_tags_in_attrs()

        f = FileMockFactory(stream=handle)

        previous = []

        with self.assertRaises(Exception) as context:
            id = ingestarticles.IngestArticlesBackgroundTask._file_upload("testuser", f, "crossref442", previous)

        self.assertTrue("Failed to upload file: Unable to validate document with identified schema;" in str(context.exception))

        issn.attrib["media_type"] = old_attr
        etree.ElementTree(root).write(ARTICLES, pretty_print=True)

    def test_60_doaj_no_issns(self):
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.save(blocking=True)

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save(blocking=True)

        job = models.BackgroundJob()

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.set_schema("doaj")
        file_upload.upload("testowner", "filename.xml")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)

        stream = Crossref442ArticleFixtureFactory.upload_no_issns()
        with open(path, "wb") as f:
            f.write(stream.read())

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        task._process(file_upload)

        assert not os.path.exists(path)

        assert file_upload.status == "failed"
        assert file_upload.error == "Unable to validate document with identified schema"

    def test_61_journal_not_indoaj(self):
        """ You can't upload an article for a journal that's been withdrawn"""
        etree.XMLSchema = self.mock_load_schema
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.set_in_doaj(False)
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
        file_upload.set_schema("crossref442")
        file_upload.upload("testowner", "filename.xml")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)

        stream = Crossref442ArticleFixtureFactory.upload_1_issn_correct()
        with open(path, "wb") as f:
            f.write(stream.read())

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        task._process(file_upload)

        assert not os.path.exists(path)

        assert file_upload.status == "failed"
        assert file_upload.error == Messages.EXCEPTION_ADDING_ARTICLE_TO_WITHDRAWN_JOURNAL
