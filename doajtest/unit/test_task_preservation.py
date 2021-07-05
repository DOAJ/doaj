import os
from io import BytesIO
from doajtest.helpers import DoajTestCase
from portality.tasks import preservation
from portality.core import app
from werkzeug.datastructures import FileStorage


class TestPreservation(DoajTestCase):

    def setUp(self):
        super(TestPreservation, self).setUp()
        self.upload_dir = app.config.get("UPLOAD_DIR", ".")
        self.preservation = preservation.Preservation("rama")

    def tearDown(self):
        super(TestPreservation, self).tearDown()
        self.preservation.delete_local_directory()

    def test_local_directory(self):

        #Test creation of local directory
        self.preservation.create_local_directory()
        assert os.path.isdir(os.path.join(self.upload_dir, self.preservation.dir_name))

        #Test deletion of local directory
        self.preservation.delete_local_directory()
        assert not os.path.exists(os.path.join(self.upload_dir, self.preservation.dir_name))

    def test_preservation(self):

        resources = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "unit", "resources")
        temp_dir = os.path.join(self.upload_dir, self.preservation.dir_name)

        articles_zip_path = os.path.join(resources,"articles.zip")
        # Test zip file save
        with open(articles_zip_path, 'rb') as zf:
            zip_file = FileStorage(BytesIO(zf.read()), filename="articles.zip")
            self.preservation.save_file(zip_file)

            assert os.path.exists(os.path.join(temp_dir, zip_file.filename))

        # Test extraction of zip file
        self.preservation.extract_zip_file()

        assert os.path.exists(os.path.join(temp_dir, "articles"))
        assert os.path.isdir(os.path.join(temp_dir, "articles"))
        assert os.path.isdir(os.path.join(temp_dir, "articles", "article_1"))
        assert os.path.exists(os.path.join(temp_dir, "articles", "article_1", "identifier.txt"))

