import os
from doajtest import test_constants
import requests
from io import BytesIO
from unittest.mock import patch
from doajtest.helpers import DoajTestCase, login
from doajtest.mocks.preservation import PreservationMock
from portality.tasks import preservation
from portality.core import app
from portality.lib import dates
from werkzeug.datastructures import FileStorage
from portality.models.article import Article
from portality.models import Account


def mock_pull_by_key(key, value):
    if value == "http://link.springer.com/article/10.1186/s40478-018-0619-9":
        article = Article()
        article.data = PreservationMock.ARTICLE_DATA
        return article
    elif value == "https://www.frontiersin.org/articles/10.3389/fcosc.2022.1028295":
        article = Article()
        article.data = PreservationMock.ARTICLE_DATA_JOURNAL2
        return article


def mock_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if not args[0] == None and kwargs["data"]["org"] == "DOAJ":
        return MockResponse({
            "files": [
                {
                    "name": "name_of_tarball.tar.gz",
                    "sha256": "decafbad"
                }
            ]
        }, 200)

    return MockResponse(None, 404)


def mock_owner_of_article(*args, **kwargs):
    return True


class TestPreservationSetup(DoajTestCase):

    def initial_setup(self, package_name):
        super(TestPreservationSetup, self).setUp()
        articles_zip_path = test_constants.PATH_RESOURCES / package_name
        with open(articles_zip_path, 'rb') as zf:
            self.zip_file = FileStorage(BytesIO(zf.read()), filename=package_name)

        self.upload_dir = app.config.get("UPLOAD_DIR", ".")
        created_time = dates.now_str("%Y-%m-%d-%H-%M-%S")
        self.owner = "rama"
        self.journal_dir = "2051-5960"
        dir_name = self.owner + "-" + created_time
        self.local_dir = os.path.join(preservation.Preservation.UPLOAD_DIR, dir_name)
        self.preserve = preservation.Preservation(self.local_dir, self.owner)
        self.tmp_dir = os.path.join(self.local_dir, "tmp")
        self.preservation_collection = app.config.get("PRESERVATION_COLLECTION")
        app.config["PRESERVATION_COLLECTION"] = {"rama": ["test", "2"]}

    def tearDown(self):
        super(TestPreservationSetup, self).tearDown()
        preservation.Preservation.delete_local_directory(self.local_dir)
        app.config["PRESERVATION_COLLECTION"] = self.preservation_collection


class TestPreservation(TestPreservationSetup):

    def setUp(self):
        super(TestPreservation, self).initial_setup("articles.zip")

    def tearDown(self):
        super(TestPreservation, self).tearDown()

    def test_local_directory(self):

        # Test creation of local directory
        # TestPreservation.preserve.create_local_directories()
        job = preservation.PreservationBackgroundTask.prepare("rama", upload_file=self.zip_file)
        params = job.params
        local_dir = params["preserve__local_dir"]
        dir_name = os.path.basename(local_dir)

        assert os.path.isdir(os.path.join(self.upload_dir, dir_name))
        assert os.path.isdir(os.path.join(self.upload_dir, dir_name,dir_name))

        # Test deletion of local directory
        preservation.Preservation.delete_local_directory(local_dir)
        assert not os.path.exists(os.path.join(self.upload_dir, dir_name))

    @patch.object(Article, 'pull_by_key', mock_pull_by_key)
    @patch.object(requests, "post", mock_requests_post)
    @patch.object(preservation.Preservation, 'owner_of_article', mock_owner_of_article)
    def test_preservation(self):
        self.preserve.save_file(self.zip_file)

        assert os.path.exists(os.path.join(self.tmp_dir, self.zip_file.filename))

        # Test extraction of zip file
        self.preserve.extract_zip_file()

        assert os.path.exists(os.path.join(self.tmp_dir, "articles"))
        assert os.path.isdir(os.path.join(self.tmp_dir, "articles"))
        assert os.path.isdir(os.path.join(self.tmp_dir, "articles", "article_1"))
        assert os.path.exists(os.path.join(self.tmp_dir, "articles",
                                           "article_1", "identifier.txt"))

        reader = preservation.CSVReader(os.path.join(self.tmp_dir,
                                                     "articles", "identifiers.csv"))
        data = reader.articles_info()

        assert "article_1" in data
        assert "article/10.1186/s40478-018-0619-9" in data["article_1"][0]

        # Test package structure
        self.preserve.create_package_structure()
        package_dir = os.path.join(self.upload_dir,
                                   self.preserve.dir_name, self.preserve.dir_name, self.journal_dir)
        tag_manifest_file = os.path.join(package_dir, "00003741594643f4996e2555a01e03c7", "tagmanifest-sha256.txt")
        manifest_file = os.path.join(package_dir, "00003741594643f4996e2555a01e03c7", "manifest-sha256.txt")
        assert os.path.exists(package_dir)
        assert os.path.exists(tag_manifest_file)
        assert os.path.exists(manifest_file)

        package = preservation.PreservationPackage(self.preserve.preservation_dir, self.journal_dir, self.owner)

        # Test creation of tar file
        package.create_package()
        tar_file = package_dir + "_" + package.created_time + ".tar.gz"
        assert os.path.exists(tar_file)

        sha256 = package.sha256(tar_file)
        response = package.upload_package(sha256, tar_file)
        assert response.status_code == 200

    def test_get_article_info(self):
        issn, article_id, metadata_json = self.preserve.get_article_info(PreservationMock.ARTICLE_DATA)

        assert issn == "2051-5960"
        assert article_id == "00003741594643f4996e2555a01e03c7"
        assert metadata_json["bibjson"]["identifier"][0]["id"] == "10.1186/s40478-018-0619-9"


class TestPreservationMultipleJournals(TestPreservationSetup):

    def setUp(self):
        super(TestPreservationMultipleJournals, self).initial_setup("preservation_multiple_journals.zip")
        self.another_journal_dir = "2673-611X"

    def tearDown(self):
        super(TestPreservationMultipleJournals, self).tearDown()

    @patch.object(Article, 'pull_by_key', mock_pull_by_key)
    @patch.object(requests, "post", mock_requests_post)
    @patch.object(preservation.Preservation, 'owner_of_article', mock_owner_of_article)
    def test_preservation_multiple_journals(self):
        self.preserve.save_file(self.zip_file)

        # Test extraction of zip file
        self.preserve.extract_zip_file()

        assert os.path.exists(os.path.join(self.tmp_dir, "articles"))
        assert os.path.isdir(os.path.join(self.tmp_dir, "articles"))
        assert os.path.isdir(os.path.join(self.tmp_dir, "articles", "article_1"))
        assert os.path.exists(os.path.join(self.tmp_dir, "articles",
                                           "article_1", "Identifier.txt"))

        reader = preservation.CSVReader(os.path.join(self.tmp_dir,
                                                     "articles", "Identifiers.csv"))
        data = reader.articles_info()

        assert "article_1" in data
        assert "article/10.1186/s40478-018-0619-9" in data["article_1"][0]

        assert "article_2" in data
        assert "10.3389/fcosc.2022.1028295" in data["article_2"][0]

        # Test package structure
        self.preserve.create_package_structure()
        package_dir = os.path.join(self.upload_dir,
                                   self.preserve.dir_name, self.preserve.dir_name, self.journal_dir)
        tag_manifest_file = os.path.join(package_dir, "00003741594643f4996e2555a01e03c7", "tagmanifest-sha256.txt")
        manifest_file = os.path.join(package_dir, "00003741594643f4996e2555a01e03c7", "manifest-sha256.txt")
        assert os.path.exists(package_dir)
        assert os.path.exists(tag_manifest_file)
        assert os.path.exists(manifest_file)

        package = preservation.PreservationPackage(self.preserve.preservation_dir, self.journal_dir, self.owner)

        # Test creation of tar file
        package.create_package()
        tar_file = package_dir + "_" + package.created_time + ".tar.gz"
        assert os.path.exists(tar_file)

        sha256 = package.sha256(tar_file)
        response = package.upload_package(sha256, tar_file)
        assert response.status_code == 200

        # Test another journal package
        package_dir = os.path.join(self.upload_dir,
                                   self.preserve.dir_name, self.preserve.dir_name, self.another_journal_dir)
        tag_manifest_file = os.path.join(package_dir, "00005741594643f4996e2666a01e0310", "tagmanifest-sha256.txt")
        manifest_file = os.path.join(package_dir, "00005741594643f4996e2666a01e0310", "manifest-sha256.txt")
        assert os.path.exists(package_dir)
        assert os.path.exists(tag_manifest_file)
        assert os.path.exists(manifest_file)

        package = preservation.PreservationPackage(self.preserve.preservation_dir, self.another_journal_dir, self.owner)

        # Test creation of tar file for another journal
        package.create_package()
        tar_file = package_dir + "_" + package.created_time + ".tar.gz"
        assert os.path.exists(tar_file)

        sha256 = package.sha256(tar_file)
        response = package.upload_package(sha256, tar_file)
        assert response.status_code == 200

    def test_get_article_info(self):
        issn, article_id, metadata_json = self.preserve.get_article_info(PreservationMock.ARTICLE_DATA)

        assert issn == "2051-5960"
        assert article_id == "00003741594643f4996e2555a01e03c7"
        assert metadata_json["bibjson"]["identifier"][0]["id"] == "10.1186/s40478-018-0619-9"

    def test_empty_file(self):
        admin_account = Account.make_account(email="admin@test.com", username="admin", name="Admin", roles=["admin"])
        admin_account.set_password('password123')
        admin_account.save()

        with self.app_test.test_client() as t_client:
            login(t_client, "admin", "password123")
            response = t_client.post('/publisher/preservation', data={})
            with t_client.session_transaction() as session:
                flash_messages = session.get('_flashes')
                assert any(msg[1] == "No file provided for upload" for msg in flash_messages)
