import os
import shutil
from datetime import datetime
from portality.core import app
from portality.lib import dates

class PreservationException(Exception):
    pass

class Preservation:

    #Zip file name to download the zip file to temp directory
    ARTICLES_ZIP_NAME = "articles.zip"

    def __init__(self):
        self.upload_dir = app.config.get("UPLOAD_DIR", ".")
        self.__created_time = dates.format(datetime.utcnow(),"%Y-%m-%d-%H-%M-%S")
        self.__dir_name = None

    @property
    def dir_name(self):
        return self.__dir_name

    def create_local_directory(self, owner):
        """
        Create a unique local directory to download the files
        :param owner: User who upload files
        :return:
        """

        # Create unique name for the directory
        self.__dir_name = owner + "-" + self.__created_time

        local_dir = os.path.join(self.upload_dir, self.__dir_name)
        os.mkdir(local_dir)

    def delete_local_directory(self):
        """Deletes the directory
        :param dir_name: Name of the directory to delete
        :return:
        """
        if self.__dir_name:
            local_dir = os.path.join(self.upload_dir, self.__dir_name)
            if os.path.exists(local_dir):
                shutil.rmtree(local_dir)

    def save_file(self, owner, file):
        """
        Save the file on to local directory
        :param owner: User who upload files
        :param file: File object
        :return:
        """
        self.create_local_directory(owner)
        local_dir = os.path.join(self.upload_dir, self.__dir_name)
        file_path = os.path.join(local_dir, Preservation.ARTICLES_ZIP_NAME)
        file.save(file_path)

