from doajtest.helpers import DoajTestCase
from lxml import etree

from doajtest.mocks.bll_article import BLLArticleMockFactory
from doajtest.mocks.ftp import FTPMockFactory
from doajtest.mocks.file import FileMockFactory
from doajtest.mocks.response import ResponseMockFactory
from doajtest.mocks.xwalk import XwalkMockFactory
from portality.tasks import ingestarticles
from doajtest.fixtures.article_doajxml import DoajXmlArticleFixtureFactory
from doajtest.fixtures.accounts import AccountFixtureFactory
import time
from portality.crosswalks import article_doaj_xml
from portality.bll.services import article as articleSvc

from portality import models
from portality.core import app

from portality.background import BackgroundException

import ftplib, os, requests
from urllib.parse import urlparse

class TestIngestArticlesDoajXML(DoajTestCase):

    @classmethod
    def setUpClass(self):

        super(TestIngestArticlesDoajXML, self).setUpClass()
        self.schema_old = etree.XMLSchema

    @classmethod
    def tearDownClass(self):
        super(TestIngestArticlesDoajXML, self).tearDownClass()
        etree.XMLSchema = self.schema_old

    def setUp(self):
        super(TestIngestArticlesDoajXML, self).setUp()

        self.cleanup_ids = []
        self.cleanup_paths = []

        self.xwalk_validate = article_doaj_xml.DOAJXWalk.validate
        self.batch_create_articles = articleSvc.ArticleService.batch_create_articles

        self.head = requests.head
        self.get = requests.get
        self.ftp = ftplib.FTP

        self.upload_dir = app.config["UPLOAD_DIR"]
        self.ingest_articles_retries = app.config['HUEY_TASKS']['ingest_articles']['retries']

        schema_path = app.config.get("SCHEMAS", {}).get("doaj")
        schema_file = open(schema_path)
        schema_doc = etree.parse(schema_file)
        self.schema = etree.XMLSchema(schema_doc)

        etree.XMLSchema = self.mock_load_schema

    def tearDown(self):
        super(TestIngestArticlesDoajXML, self).tearDown()

        article_doaj_xml.DOAJXWalk.validate = self.xwalk_validate
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


    def mock_load_schema(self, doc):
        return self.schema

    def test_01_doaj_file_upload_success(self):

        handle = DoajXmlArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)

        previous = []
        id = ingestarticles.IngestArticlesBackgroundTask._file_upload("testuser", f, "doaj", previous)
        self.cleanup_ids.append(id)

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.schema == "doaj"
        assert fu.status == "validated"

        path = os.path.join(app.config.get("UPLOAD_DIR", "."), id + ".xml")
        assert os.path.exists(path)

        assert len(previous) == 1


    def test_02_doaj_file_upload_invalid(self):

        handle = DoajXmlArticleFixtureFactory.invalid_schema_xml()
        f = FileMockFactory(stream=handle)

        previous = []
        with self.assertRaises(BackgroundException):
            id = ingestarticles.IngestArticlesBackgroundTask._file_upload("testuser", f, "doaj", previous)

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

    def test_03_doaj_file_upload_fail(self):

        article_doaj_xml.DOAJXWalk.validate = XwalkMockFactory.validate
        etree.XMLSchema = self.mock_load_schema

        handle = DoajXmlArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)

        previous = []
        with self.assertRaises(BackgroundException):
            id = ingestarticles.IngestArticlesBackgroundTask._file_upload("testuser", f, "doaj", previous)

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

    def test_04_doaj_url_upload_http_success(self):
        # first try with a successful HEAD request
        requests.head = ResponseMockFactory.head_success
        requests.get = ResponseMockFactory.doaj_get_success

        url = "http://success"
        previous = []

        id = ingestarticles.IngestArticlesBackgroundTask._url_upload("testuser", url, "doaj", previous)

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.schema == "doaj"
        assert fu.status == "exists"

        assert len(previous) == 1

        # try that again, but with an unsuccessful HEAD request
        requests.head = ResponseMockFactory.head_fail

        previous = []

        id = ingestarticles.IngestArticlesBackgroundTask._url_upload("testuser", url, "doaj", previous)

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.schema == "doaj"
        assert fu.status == "exists"

        assert len(previous) == 1

    def test_05_doaj_url_upload_http_fail(self):
        # try with failing http requests
        requests.head = ResponseMockFactory.head_fail
        requests.get = ResponseMockFactory.get_fail

        url = "http://fail"
        previous = []

        with self.assertRaises(BackgroundException):
            id = ingestarticles.IngestArticlesBackgroundTask._url_upload("testuser", url, "doaj", previous)

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
            id = ingestarticles.IngestArticlesBackgroundTask._url_upload("testuser", url, "doaj", previous)

        assert len(previous) == 1
        id = previous[0].id

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.status == "failed"
        assert fu.error is not None and fu.error != ""
        assert fu.error_details is None
        assert list(fu.failure_reasons.keys()) == []

    def test_06_doaj_url_upload_ftp_success(self):
        ftplib.FTP = FTPMockFactory.create("doaj")

        url = "ftp://success"

        previous = []

        id = ingestarticles.IngestArticlesBackgroundTask._url_upload("testuser", url, "doaj", previous)

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.schema == "doaj"
        assert fu.status == "exists"

        assert len(previous) == 1

    def test_07_url_upload_ftp_fail(self):
        ftplib.FTP = FTPMockFactory.create("doaj")

        url = "ftp://fail"

        previous = []

        with self.assertRaises(BackgroundException):
            id = ingestarticles.IngestArticlesBackgroundTask._url_upload("testuser", url, "doaj", previous)

        assert len(previous) == 1
        id = previous[0].id

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.status == "failed"
        assert fu.error is not None and fu.error != ""
        assert fu.error_details is None
        assert list(fu.failure_reasons.keys()) == []

    def test_08_doajxml_prepare_file_upload_success(self):

        handle = DoajXmlArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)

        previous = []
        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testuser", upload_file=f, schema="doaj", previous=previous)

        assert job is not None
        assert "ingest_articles__file_upload_id" in job.params
        id = job.params.get("ingest_articles__file_upload_id")
        self.cleanup_ids.append(id)

        assert len(previous) == 1

        fu = models.FileUpload.pull(id)
        assert fu is not None

    def test_09_prepare_file_upload_fail(self):

        article_doaj_xml.DOAJXWalk.validate = XwalkMockFactory.validate

        handle = DoajXmlArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)

        previous = []
        with self.assertRaises(BackgroundException):
            job = ingestarticles.IngestArticlesBackgroundTask.prepare("testuser", upload_file=f, schema="doaj", previous=previous)

        assert len(previous) == 1
        id = previous[0].id
        self.cleanup_ids.append(id)

        fu = models.FileUpload.pull(id)
        assert fu is not None

    def test_10_prepare_url_upload_success(self):
        requests.head = ResponseMockFactory.head_success
        requests.get = ResponseMockFactory.doaj_get_success

        url = "http://success"

        previous = []

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testuser", url=url, schema="doaj", previous=previous)

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

        with self.assertRaises(BackgroundException):
            job = ingestarticles.IngestArticlesBackgroundTask.prepare("testuser", url=url, schema="doaj", previous=previous)

        assert len(previous) == 1
        id = previous[0].id
        self.cleanup_ids.append(id)

        fu = models.FileUpload.pull(id)
        assert fu is not None

    def test_12_prepare_parameter_errors(self):
        # no url or file upload

        with self.assertRaises(BackgroundException):
            job = ingestarticles.IngestArticlesBackgroundTask.prepare("testuser", schema="doaj", previous=[])

        # no schema
        with self.assertRaises(BackgroundException):
            job = ingestarticles.IngestArticlesBackgroundTask.prepare("testuser", url="http://whatever", previous=[])

        # upload dir not configured
        del app.config["UPLOAD_DIR"]
        with self.assertRaises(BackgroundException):
            job = ingestarticles.IngestArticlesBackgroundTask.prepare("testuser", url="http://whatever", schema="doaj", previous=[])

    def test_13_ftp_upload_success(self):
        ftplib.FTP = FTPMockFactory.create("doaj")

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
        ftplib.FTP = FTPMockFactory.create("doaj")

        file_upload = models.FileUpload()
        file_upload.set_id()

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)

        url= "ftp://fail"
        parsed_url = urlparse(url)

        job = models.BackgroundJob()

        result = ingestarticles.ftp_upload(job, path, parsed_url, file_upload)

        assert result is False
        assert file_upload.status == "failed"
        assert file_upload.error is not None and file_upload.error != ""
        assert file_upload.error_details is None
        assert list(file_upload.failure_reasons.keys()) == []

    def test_15_http_upload_success(self):
        requests.head = ResponseMockFactory.head_fail
        requests.get = ResponseMockFactory.doaj_get_success

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

    def test_17_doaj_download_http_valid(self):
        requests.head = ResponseMockFactory.head_fail
        requests.get = ResponseMockFactory.doaj_get_success

        job = models.BackgroundJob()
        task = ingestarticles.IngestArticlesBackgroundTask(job)

        url = "http://valid"

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.upload("testuser", url, status="exists")
        file_upload.set_schema("doaj")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)
        print(file_upload)

        result = task._download(file_upload)

        assert result is True
        assert file_upload.status == "validated"

    def test_18_download_http_invalid(self):
        requests.head = ResponseMockFactory.head_fail
        requests.get = ResponseMockFactory.doaj_get_success

        job = models.BackgroundJob()

        url = "http://upload"

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.upload("testuser", url, status="exists")
        file_upload.set_schema("doaj")

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
        requests.head = ResponseMockFactory.head_fail
        requests.get = ResponseMockFactory.get_fail

        job = models.BackgroundJob()

        url = "http://fail"

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.upload("testuser", url, status="exists")
        file_upload.set_schema("doaj")

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
        ftplib.FTP = FTPMockFactory.create("doaj")

        job = models.BackgroundJob()

        url = "ftp://valid"

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.upload("testuser", url, status="exists")
        file_upload.set_schema("doaj")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        result = task._download(file_upload)

        assert result is True
        assert file_upload.status == "validated"

    def test_21_download_ftp_invalid(self):
        ftplib.FTP = FTPMockFactory.create("doaj")

        job = models.BackgroundJob()

        url = "ftp://upload"

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.upload("testuser", url, status="exists")
        file_upload.set_schema("doaj")

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
        ftplib.FTP = FTPMockFactory.create("doaj")

        job = models.BackgroundJob()

        url = "ftp://fail"

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.upload("testuser", url, status="exists")
        file_upload.set_schema("doaj")

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

    def test_23_doaj_process_success(self):

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

        stream = DoajXmlArticleFixtureFactory.upload_1_issn_correct()
        with open(path, "wb") as f:
            f.write(stream.read())

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        task._process(file_upload)

        assert not os.path.exists(path)

        assert file_upload.status == "processed"
        assert file_upload.imported == 1
        assert file_upload.new == 1

    def test_24_process_invalid_file(self):
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.save(blocking=True)

        job = models.BackgroundJob()

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.set_schema("doaj")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)
        self.cleanup_ids.append(file_upload.id)

        stream = DoajXmlArticleFixtureFactory.invalid_schema_xml()
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
        articleSvc.ArticleService.batch_create_articles = BLLArticleMockFactory.batch_create

        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.save(blocking=True)

        job = models.BackgroundJob()

        file_upload = models.FileUpload()
        file_upload.set_id()
        file_upload.set_schema("doaj")

        upload_dir = app.config.get("UPLOAD_DIR")
        path = os.path.join(upload_dir, file_upload.local_filename)
        self.cleanup_paths.append(path)
        self.cleanup_ids.append(file_upload.id)

        stream = DoajXmlArticleFixtureFactory.upload_1_issn_correct()
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
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.save(blocking=True)

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save(blocking=True)

        handle = DoajXmlArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)

        previous = []

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", upload_file=f, schema="doaj", previous=previous)
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
        requests.head = ResponseMockFactory.head_fail
        requests.get = ResponseMockFactory.doaj_get_success

        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.save(blocking=True)

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save(blocking=True)

        url = "http://valid"

        previous = []

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", url=url, schema="doaj", previous=previous)
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

    def test_28_run_errors(self):
        job = models.BackgroundJob()
        task = ingestarticles.IngestArticlesBackgroundTask(job)

        with self.assertRaises(BackgroundException):
            task.run()

        job.params = {}

        with self.assertRaises(BackgroundException):
            task.run()

        job.params = {"ingest_articles__file_upload_id" : "whatever"}

        with self.assertRaises(BackgroundException):
            task.run()

    def test_29_submit_success(self):
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.save(blocking=True)

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save(blocking=True)

        handle = DoajXmlArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)

        previous = []

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", upload_file=f, schema="doaj", previous=previous)
        id = job.params.get("ingest_articles__file_upload_id")
        self.cleanup_ids.append(id)

        # because file upload gets created and saved by prepare
        time.sleep(2)

        # this assumes that huey is in always eager mode, and thus this immediately calls the async task,
        # which in turn calls execute, which ultimately calls run
        ingestarticles.IngestArticlesBackgroundTask.submit(job)

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.status == "processed"

    def test_31_doaj_run_fail_unmatched_issn(self):
        # Create a journal with 2 issns, one of which is the same as an issn on the
        # article, but the article also contains an issn which doesn't match the journal
        # We expect a failed ingest

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

        handle = DoajXmlArticleFixtureFactory.upload_2_issns_ambiguous()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="doaj", upload_file=f)
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

    def test_32_run_doaj_fail_shared_issn(self):
        # Create 2 journals with the same issns but different owners, which match the issns on the article
        # We expect an ingest failure

        j1 = models.Journal()
        j1.set_owner("testowner1")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        bj1.add_identifier(bj1.E_ISSN, "9876-5432")
        j1.save()

        j2 = models.Journal()
        j2.set_owner("testowner2")
        j2.set_in_doaj(False)
        bj2 = j2.bibjson()
        bj2.add_identifier(bj2.P_ISSN, "1234-5678")
        bj2.add_identifier(bj2.E_ISSN, "9876-5432")
        j2.save(blocking=True)

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner1")
        account.save(blocking=True)

        handle = DoajXmlArticleFixtureFactory.upload_2_issns_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner1", schema="doaj", upload_file=f)
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

        j1 = models.Journal()
        j1.set_owner("testowner1")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        j1.save()

        j2 = models.Journal()
        j2.set_owner("testowner2")
        j2.set_in_doaj(False)
        bj2 = j2.bibjson()
        bj2.add_identifier(bj2.E_ISSN, "9876-5432")
        j2.save(blocking=True)

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save(blocking=True)

        handle = DoajXmlArticleFixtureFactory.upload_2_issns_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="doaj", upload_file=f)
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

    def test_34_doaj_journal_2_article_2_success(self):
        # Create a journal with two issns both of which match the 2 issns in the article
        # we expect a successful article ingest
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

        handle = DoajXmlArticleFixtureFactory.upload_2_issns_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="doaj", upload_file=f)
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

    def test_35_doaj_journal_2_article_1_success(self):
        # Create a journal with 2 issns, one of which is present in the article as the
        # only issn
        # We expect a successful article ingest
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        bj.add_identifier(bj.E_ISSN, "9876-5432")
        j.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save(blocking=True)

        handle = DoajXmlArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="doaj", upload_file=f)
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

    def test_37_doaj_journal_1_article_1_success(self):
        # Create a journal with 1 issn, which is the same 1 issn on the article
        # we expect a successful article ingest
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save(blocking=True)

        handle = DoajXmlArticleFixtureFactory.upload_1_issn_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="doaj", upload_file=f)
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

    def test_38_doaj_journal_2_article_2_1_different_success(self):
        # Create a journal with 2 issns, one of which is the same as an issn on the
        # article, but the article also contains an issn which doesn't match the journal
        # We expect a failed ingest
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        bj.add_identifier(bj.E_ISSN, "9876-5432")
        j.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save(blocking=True)

        handle = DoajXmlArticleFixtureFactory.upload_2_issns_ambiguous()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="doaj", upload_file=f)
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

    def test_39_doaj_2_journals_different_owners_both_issns_fail(self):
        # Create 2 journals with the same issns but different owners, which match the issns on the article
        # We expect an ingest failure
        j1 = models.Journal()
        j1.set_owner("testowner1")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        bj1.add_identifier(bj1.E_ISSN, "9876-5432")
        j1.save()

        j2 = models.Journal()
        j2.set_owner("testowner2")
        j2.set_in_doaj(False)
        bj2 = j2.bibjson()
        bj2.add_identifier(bj2.P_ISSN, "1234-5678")
        bj2.add_identifier(bj2.E_ISSN, "9876-5432")
        j2.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner1")
        account.save(blocking=True)

        handle = DoajXmlArticleFixtureFactory.upload_2_issns_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner1", schema="doaj", upload_file=f)
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

    def test_40_doaj_2_journals_different_owners_issn_each_fail(self):
        # Create 2 journals with different owners and one different issn each.  The two issns in the
        # article match each of the journals respectively
        # We expect an ingest failure
        j1 = models.Journal()
        j1.set_owner("testowner1")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        j1.save()

        j2 = models.Journal()
        j2.set_owner("testowner2")
        j2.set_in_doaj(False)
        bj2 = j2.bibjson()
        bj2.add_identifier(bj2.E_ISSN, "9876-5432")
        j2.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner1")
        account.save(blocking=True)

        handle = DoajXmlArticleFixtureFactory.upload_2_issns_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner1", schema="doaj", upload_file=f)
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

    def test_41_doaj_2_journals_same_owner_issn_each_success(self):
        # Create 2 journals with the same owner, each with one different issn.  The article's 2 issns
        # match each of these issns
        # We expect a successful article ingest
        j1 = models.Journal()
        j1.set_owner("testowner")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        j1.save()

        j2 = models.Journal()
        j2.set_owner("testowner")
        j2.set_in_doaj(False)
        bj2 = j2.bibjson()
        bj2.add_identifier(bj2.E_ISSN, "9876-5432")
        j2.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save(blocking=True)

        handle = DoajXmlArticleFixtureFactory.upload_2_issns_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="doaj", upload_file=f)
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

    def test_42_doaj_2_journals_different_owners_different_issns_mixed_article_fail(self):
        # Create 2 different journals with different owners and different issns (2 each).
        # The article's issns match one issn in each journal
        # We expect an ingest failure
        j1 = models.Journal()
        j1.set_owner("testowner1")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        bj1.add_identifier(bj1.E_ISSN, "2345-6789")
        j1.save()

        j2 = models.Journal()
        j2.set_owner("testowner2")
        j2.set_in_doaj(False)
        bj2 = j2.bibjson()
        bj2.add_identifier(bj2.P_ISSN, "8765-4321")
        bj2.add_identifier(bj2.E_ISSN, "9876-5432")
        j2.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner1")
        account.save(blocking=True)

        handle = DoajXmlArticleFixtureFactory.upload_2_issns_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner1", schema="doaj", upload_file=f)
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

    def test_43_doaj_duplication(self):
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        bj.add_identifier(bj.E_ISSN, "9876-5432")
        j.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save(blocking=True)

        # make both handles, as we want as little gap as possible between requests in a moment
        handle1 = DoajXmlArticleFixtureFactory.upload_2_issns_correct()
        handle2 = DoajXmlArticleFixtureFactory.upload_2_issns_correct()

        f1 = FileMockFactory(stream=handle1)
        f2 = FileMockFactory(stream=handle2)

        job1 = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="doaj", upload_file=f1)
        id1 = job1.params.get("ingest_articles__file_upload_id")
        self.cleanup_ids.append(id1)

        job2 = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="doaj", upload_file=f2)
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

    def test_44_doaj_journal_1_article_1_superlong_noclip(self):
        # Create a journal with 1 issn, which is the same 1 issn on the article
        # we expect a successful article ingest
        # But it's just shy of 30000 unicode characters long!
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save(blocking=True)

        handle = DoajXmlArticleFixtureFactory.upload_1_issn_superlong_should_not_clip()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="doaj", upload_file=f)
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
        assert len(found[0].bibjson().abstract) == 26264

    def test_doaj_45_journal_1_article_1_superlong_clip(self):
        # Create a journal with 1 issn, which is the same 1 issn on the article
        # we expect a successful article ingest
        # But it's over 40k unicode characters long!
        j = models.Journal()
        j.set_owner("testowner")
        bj = j.bibjson()
        bj.add_identifier(bj.P_ISSN, "1234-5678")
        j.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner")
        account.save(blocking=True)

        handle = DoajXmlArticleFixtureFactory.upload_1_issn_superlong_should_clip()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner", schema="doaj", upload_file=f)
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

    def test_46_doaj_one_journal_one_article_2_issns_one_unknown(self):
        # Create one journal and ingest one article.  The Journal has two issns, and the article
        # has two issns, but one of the journal's issns is unknown
        # We expect an ingest failure
        j1 = models.Journal()
        j1.set_owner("testowner1")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        bj1.add_identifier(bj1.P_ISSN, "2222-2222")
        j1.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner1")
        account.save(blocking=True)

        handle = DoajXmlArticleFixtureFactory.upload_2_issns_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner1", schema="doaj", upload_file=f)
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
        assert "9876-5432" in fr["unmatched"]

        found = [a for a in models.Article.find_by_issns(["1234-5678", "9876-5432"])]
        assert len(found) == 0

    def test_47_doaj_lcc_spelling_error(self):
        # create a journal with a broken subject classification
        j1 = models.Journal()
        j1.set_owner("testowner1")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        bj1.add_identifier(bj1.P_ISSN, "9876-5432")
        bj1.add_subject("LCC", "Whatever", "WHATEVA")
        bj1.add_subject("LCC", "Aquaculture. Fisheries. Angling", "SH1-691")
        j1.save()

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner1")
        account.save(blocking=True)

        handle = DoajXmlArticleFixtureFactory.upload_2_issns_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner1", schema="doaj", upload_file=f)
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

        cpaths = found[0].data["index"]["classification_paths"]
        assert len(cpaths) == 1
        assert cpaths[0] == "Agriculture: Aquaculture. Fisheries. Angling"

    def test_48_doaj_unknown_journal_issn(self):
        # create a journal with one of the ISSNs specified
        j1 = models.Journal()
        j1.set_owner("testowner1")
        bj1 = j1.bibjson()
        bj1.add_identifier(bj1.P_ISSN, "1234-5678")
        j1.save(blocking=True)

        asource = AccountFixtureFactory.make_publisher_source()
        account = models.Account(**asource)
        account.set_id("testowner1")
        account.save(blocking=True)

        # take an article with 2 issns, but one of which is not in the index
        handle = DoajXmlArticleFixtureFactory.upload_2_issns_correct()
        f = FileMockFactory(stream=handle)

        job = ingestarticles.IngestArticlesBackgroundTask.prepare("testowner1", schema="doaj", upload_file=f)
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


    def test_49_doaj_noids(self):
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

        stream = DoajXmlArticleFixtureFactory.noids()
        with open(path, "wb") as f:
            f.write(stream.read())

        task = ingestarticles.IngestArticlesBackgroundTask(job)
        task._process(file_upload)

        assert not os.path.exists(path)

        assert file_upload.status == "failed"

    def test_50_valid_url_starting_with_http(self):
        handle = DoajXmlArticleFixtureFactory.valid_url_http()
        f = FileMockFactory(stream=handle)

        previous = []
        id = ingestarticles.IngestArticlesBackgroundTask._file_upload("testuser", f, "doaj", previous)
        self.cleanup_ids.append(id)

        fu = models.FileUpload.pull(id)

        assert fu.status == "validated"

    def test_51_valid_url_starting_with_https(self):
        handle = DoajXmlArticleFixtureFactory.valid_url_https()
        f = FileMockFactory(stream=handle)

        previous = []
        id = ingestarticles.IngestArticlesBackgroundTask._file_upload("testuser", f, "doaj", previous)
        self.cleanup_ids.append(id)

        fu = models.FileUpload.pull(id)

        assert fu.status == "validated"

    def test_52_valid_url_with_non_ascii_chars(self):
        handle = DoajXmlArticleFixtureFactory.valid_url_non_ascii_chars()
        f = FileMockFactory(stream=handle)

        previous = []
        id = ingestarticles.IngestArticlesBackgroundTask._file_upload("testuser", f, "doaj", previous)
        self.cleanup_ids.append(id)

        fu = models.FileUpload.pull(id)
        assert fu.status == "validated"

    def test_53_invalid_url(self):
        handle = DoajXmlArticleFixtureFactory.invalid_url()
        f = FileMockFactory(stream=handle)

        previous = []
        with self.assertRaises(BackgroundException):
            id = ingestarticles.IngestArticlesBackgroundTask._file_upload("testuser", f, "doaj", previous)

        assert len(previous) == 1
        id = previous[0].id
        self.cleanup_ids.append(id)

        fu = models.FileUpload.pull(id)

        assert fu.status == "failed"
        assert fu.error == 'Unable to validate document with identified schema'

    def test_54_invalid_url_http_missing(self):
        handle = DoajXmlArticleFixtureFactory.invalid_url_http_missing()
        f = FileMockFactory(stream=handle)

        previous = []
        with self.assertRaises(BackgroundException):
            id = ingestarticles.IngestArticlesBackgroundTask._file_upload("testuser", f, "doaj", previous)

        assert len(previous) == 1
        id = previous[0].id
        self.cleanup_ids.append(id)

        fu = models.FileUpload.pull(id)

        assert fu.status == "failed"
        assert fu.error == 'Unable to validate document with identified schema'

    def test_55_valid_url_with_http_anchor(self):
        handle = DoajXmlArticleFixtureFactory.valid_url_http_anchor()
        f = FileMockFactory(stream=handle)

        previous = []
        id = ingestarticles.IngestArticlesBackgroundTask._file_upload("testuser", f, "doaj", previous)
        self.cleanup_ids.append(id)

        fu = models.FileUpload.pull(id)
        assert fu.status == "validated"

    def test_56_valid_url_with_parameters(self):
        handle = DoajXmlArticleFixtureFactory.valid_url_parameters()
        f = FileMockFactory(stream=handle)

        previous = []
        id = ingestarticles.IngestArticlesBackgroundTask._file_upload("testuser", f, "doaj", previous)
        self.cleanup_ids.append(id)

        fu = models.FileUpload.pull(id)
        assert fu.status == "validated"

    def test_57_file_with_valid_orcid_id(self):
        handle = DoajXmlArticleFixtureFactory.valid_orcid_id()
        f = FileMockFactory(stream=handle)

        previous = []
        id = ingestarticles.IngestArticlesBackgroundTask._file_upload("testuser", f, "doaj", previous)
        self.cleanup_ids.append(id)

        fu = models.FileUpload.pull(id)
        assert fu is not None
        assert fu.schema == "doaj"
        assert fu.status == "validated"

        path = os.path.join(app.config.get("UPLOAD_DIR", "."), id + ".xml")
        assert os.path.exists(path)

        assert len(previous) == 1

    def test_58_file_with_invalid_orcid_id(self):
        handle = DoajXmlArticleFixtureFactory.invalid_orcid_id()
        f = FileMockFactory(stream=handle)

        previous = []
        with self.assertRaises(BackgroundException):
            id = ingestarticles.IngestArticlesBackgroundTask._file_upload("testuser", f, "doaj", previous)

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