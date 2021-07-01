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
        self.preservation = preservation.Preservation()

    def tearDown(self):
        super(TestPreservation, self).tearDown()
        self.preservation.delete_local_directory()

    def test_local_directory(self):

        #Test creation of local directory
        self.preservation.create_local_directory("rama")
        assert os.path.isdir(os.path.join(self.upload_dir, self.preservation.dir_name))

        #Test deletion of local directory
        self.preservation.delete_local_directory()
        assert not os.path.exists(os.path.join(self.upload_dir, self.preservation.dir_name))

    def test_save_file(self):

        resources = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "unit", "resources")

        articles_zip_path = os.path.join(resources,"articles.zip")
        with open(articles_zip_path, 'rb') as zf:
            zip_file = FileStorage(BytesIO(zf.read()), filename="articles.zip")
            self.preservation.save_file("rama", zip_file)

            assert os.path.exists(os.path.join(self.upload_dir, self.preservation.dir_name, zip_file.filename))


