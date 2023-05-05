import os
from doajtest import test_constants
import requests
from io import BytesIO
from unittest.mock import patch
from doajtest.helpers import DoajTestCase
from doajtest.mocks.preservation import PreservationMock
from portality.tasks import preservation
from portality.core import app
from portality.lib import dates
from werkzeug.datastructures import FileStorage
from portality.models.article import Article


class TestPreservation(DoajTestCase):

    def setUp(self):
        super(TestPreservation, self).setUp()
        articles_zip_path = os.path.join(test_constants.PATH_RESOURCES, "articles.zip")
        with open(articles_zip_path, 'rb') as zf:
            self.zip_file = FileStorage(BytesIO(zf.read()), filename="articles.zip")

        self.upload_dir = app.config.get("UPLOAD_DIR", ".")
        created_time = dates.now_str("%Y-%m-%d-%H-%M-%S")
        owner = "rama"
        dir_name = owner + "-" + created_time
        self.local_dir = os.path.join(preservation.Preservation.UPLOAD_DIR, dir_name)
        self.preserve = preservation.Preservation(self.local_dir, owner)
        self.package = preservation.PreservationPackage(self.preserve.preservation_dir, owner)
        self.local_dir = os.path.join(self.local_dir,"tmp")
        self.preservation_collection = app.config.get("PRESERVATION_COLLECTION")
        app.config["PRESERVATION_COLLECTION"] = {"rama":["test","2"]}

    def tearDown(self):
        super(TestPreservation, self).tearDown()
        preservation.Preservation.delete_local_directory(self.local_dir)
        app.config["PRESERVATION_COLLECTION"] = self.preservation_collection

    def test_local_directory(self):

        #Test creation of local directory
        #TestPreservation.preserve.create_local_directories()
        job = preservation.PreservationBackgroundTask.prepare("rama", upload_file=self.zip_file)
        params = job.params
        local_dir = params["preserve__local_dir"]
        dir_name = os.path.basename(local_dir)

        assert os.path.isdir(os.path.join(self.upload_dir, dir_name))
        assert os.path.isdir(os.path.join(self.upload_dir, dir_name,dir_name))

        #Test deletion of local directory
        preservation.Preservation.delete_local_directory(local_dir)
        assert not os.path.exists(os.path.join(self.upload_dir, dir_name))

    def mock_pull_by_key(key, value):
        article = Article()
        article.data = PreservationMock.ARTICLE_DATA
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

    @patch.object(Article, 'pull_by_key', mock_pull_by_key)
    @patch.object(requests,"post", mock_requests_post)
    @patch.object(preservation.Preservation, 'owner_of_article', mock_owner_of_article)
    def test_preservation(self):
        self.preserve.save_file(self.zip_file)

        assert os.path.exists(os.path.join(self.local_dir, self.zip_file.filename))

        # Test extraction of zip file
        self.preserve.extract_zip_file()

        assert os.path.exists(os.path.join(self.local_dir, "articles"))
        assert os.path.isdir(os.path.join(self.local_dir, "articles"))
        assert os.path.isdir(os.path.join(self.local_dir, "articles", "article_1"))
        assert os.path.exists(os.path.join(self.local_dir, "articles",
                                           "article_1", "identifier.txt"))

        reader = preservation.CSVReader(os.path.join(self.local_dir,
                                                     "articles", "identifiers.csv"))
        data = reader.articles_info()

        assert "article_1" in data
        assert "article/10.1186/s40478-018-0619-9" in data["article_1"][0]

        # Test package structure
        self.preserve.create_package_structure()
        package_dir = os.path.join(self.upload_dir,
                                   self.preserve.dir_name, self.preserve.dir_name)
        tag_manifest_file = os.path.join(package_dir, "2051-5960", "00003741594643f4996e2555a01e03c7", "tagmanifest-sha256.txt")
        manifest_file = os.path.join(package_dir,"2051-5960", "00003741594643f4996e2555a01e03c7", "manifest-sha256.txt")
        assert os.path.exists(package_dir)
        assert os.path.exists(tag_manifest_file)
        assert os.path.exists(manifest_file)

        # Test creation of tar file
        self.package.create_package()
        assert os.path.exists(package_dir + ".tar.gz")

        sha256 = self.package.sha256()
        response = self.package.upload_package(sha256)
        assert response.status_code == 200


    def test_get_article_info(self):
        issn, article_id, metadata_json = self.preserve.get_article_info(PreservationMock.ARTICLE_DATA)

        assert issn == "2051-5960"
        assert article_id == "00003741594643f4996e2555a01e03c7"
        assert metadata_json["bibjson"]["identifier"][0]["id"] == "10.1186/s40478-018-0619-9"
