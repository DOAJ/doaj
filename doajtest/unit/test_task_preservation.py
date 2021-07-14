import os
from io import BytesIO
from unittest.mock import patch
from doajtest.helpers import DoajTestCase
from doajtest.mocks.preservation import PreservationMock
from portality.tasks import preservation
from portality.core import app
from werkzeug.datastructures import FileStorage
from portality.models.article import Article


class TestPreservation(DoajTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestPreservation, cls).setUpClass()
        cls.upload_dir = app.config.get("UPLOAD_DIR", ".")
        cls.preserve = preservation.Preservation("rama")

    @classmethod
    def tearDownClass(cls):
        super(TestPreservation, cls).tearDownClass()
        cls.preserve.delete_local_directory()

    def setUp(self):
        super(TestPreservation, self).setUp()


    def tearDown(self):
        super(TestPreservation, self).tearDown()


    def test_local_directory(self):

        #Test creation of local directory
        TestPreservation.preserve.create_local_directories()
        assert os.path.isdir(os.path.join(TestPreservation.upload_dir, TestPreservation.preserve.dir_name))
        assert os.path.isdir(os.path.join(TestPreservation.upload_dir, TestPreservation.preserve.dir_name,
                                          TestPreservation.preserve.dir_name))

        #Test deletion of local directory
        TestPreservation.preserve.delete_local_directory()
        assert not os.path.exists(os.path.join(TestPreservation.upload_dir, TestPreservation.preserve.dir_name))

    def mock_pull_by_key(key, value):
        article = Article()
        article.data = PreservationMock.ARTICLE_DATA
        return article

    @patch.object(Article, 'pull_by_key', mock_pull_by_key)
    def test_preservation(self):

        resources = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "unit", "resources")
        temp_dir = os.path.join(TestPreservation.upload_dir, TestPreservation.preserve.dir_name)

        articles_zip_path = os.path.join(resources,"articles.zip")
        # Test zip file save
        with open(articles_zip_path, 'rb') as zf:
            zip_file = FileStorage(BytesIO(zf.read()), filename="articles.zip")
            TestPreservation.preserve.save_file(zip_file)

            assert os.path.exists(os.path.join(temp_dir, zip_file.filename))

        # Test extraction of zip file
        TestPreservation.preserve.extract_zip_file()

        assert os.path.exists(os.path.join(temp_dir, "articles"))
        assert os.path.isdir(os.path.join(temp_dir, "articles"))
        assert os.path.isdir(os.path.join(temp_dir, "articles", "article_1"))
        assert os.path.exists(os.path.join(temp_dir, "articles", "article_1", "identifier.txt"))

        reader = preservation.CSVReader(os.path.join(temp_dir, "articles", "identifiers.csv"))
        data = reader.articles_info()

        assert "article_1" in data
        assert "article/10.1186/s40478-018-0619-9" in data["article_1"][0]

        # Test package structure
        TestPreservation.preserve.create_package_structure()
        package_dir = os.path.join(TestPreservation.upload_dir,
                                        TestPreservation.preserve.dir_name, TestPreservation.preserve.dir_name)
        tag_manifest_file = os.path.join(package_dir, "2051-5960", "00003741594643f4996e2555a01e03c7", "tagmanifest-sha256.txt")
        manifest_file = os.path.join(package_dir,"2051-5960", "00003741594643f4996e2555a01e03c7", "manifest-sha256.txt")
        assert os.path.exists(package_dir)
        assert os.path.exists(tag_manifest_file)
        assert os.path.exists(manifest_file)



    def test_get_article_info(self):
        issn, article_id, metadata_json = TestPreservation.preserve.get_article_info(PreservationMock.ARTICLE_DATA)

        assert issn == "2051-5960"
        assert article_id == "00003741594643f4996e2555a01e03c7"
        assert metadata_json["bibjson"]["identifier"][0]["id"] == "10.1186/s40478-018-0619-9"
