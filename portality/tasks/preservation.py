import os
import shutil
from datetime import datetime
from zipfile import ZipFile
from portality.core import app
from portality.lib import dates

class PreservationException(Exception):
    pass


class PreservationStorageException(Exception):
    pass


class Preservation:

    #Zip file name to download the zip file to temp directory
    ARTICLES_ZIP_NAME = "articles.zip"
    #Temp directory
    UPLOAD_DIR = app.config.get("UPLOAD_DIR", ".")

    def __init__(self, owner):
        self.__created_time = dates.format(datetime.utcnow(),"%Y-%m-%d-%H-%M-%S")
        self.__dir_name = owner + "-" + self.__created_time
        self.__local_dir = os.path.join(Preservation.UPLOAD_DIR, self.__dir_name)

    @property
    def dir_name(self):
        return self.__dir_name

    def create_local_directory(self):
        """
        Create a local directory to download the files
        :param owner: User who upload files
        :return:
        """
        try:
            os.mkdir(self.__local_dir)
        except OSError as exp:
            raise PreservationStorageException(message="Could not create temp directory", inner=exp)

    def delete_local_directory(self):
        """Deletes the directory
        :param dir_name: Name of the directory to delete
        :return:
        """
        if os.path.exists(self.__local_dir):
            try:
                shutil.rmtree(self.__local_dir)
            except Exception as e:
                raise PreservationStorageException(message="Could not delete Temp directory", inner=e)

    def save_file(self, file):
        """
        Save the file on to local directory
        :param owner: User who upload files
        :param file: File object
        :return:
        """
        self.create_local_directory()
        file_path = os.path.join(self.__local_dir, Preservation.ARTICLES_ZIP_NAME)
        try:
            file.save(file_path)
        except Exception as e:
            raise PreservationStorageException(message="Could not save file in Temp directory", inner=e)

    def extract_zip_file(self):
        """
        Extracts zip file in the Temp directory
        :return:
        """
        file_path = os.path.join(self.__local_dir, Preservation.ARTICLES_ZIP_NAME)

        if os.path.exists(file_path):
            with ZipFile(file_path, 'r') as zFile:
                zFile.extractall(self.__local_dir)
        else:
            raise PreservationException(message="Could not find zip file at Temp directory")

