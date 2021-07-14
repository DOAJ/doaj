import bagit
import csv
import json
import os
import shutil
from copy import deepcopy
from datetime import datetime
from zipfile import ZipFile
from portality.core import app
from portality.lib import dates
from portality.models import Article
from portality.regex import DOI_COMPILED, HTTP_URL_COMPILED

class PreservationException(Exception):
    pass


class PreservationStorageException(Exception):
    pass

class CSVReader:

    # column names for csv file.
    # Given more identifiers just to handle any mistakes by user like empty identifiers
    # Max expected identifier are 2 (Full Text URL, DOI) in any order
    FIELD_DIR = "dir_name"
    FIELDS = (FIELD_DIR,"id_1","id_2","id_3","id_4")

    def __init__(self, csv_file):
        self.__csv_file = csv_file

    def articles_info(self):
        """
        Reads the csv file and returns dictionary with first column(directory name) as keys
        and remaining columns as array elements.

        Ex: {'article_1': ['http://link.springer.com/article/10.1186/s40478-018-0619-9',
            '10.1136/bmjophth-2021-000774'], 'article_2': ['10.1136/bmjophth-2021-000775']}

        :return: Dictionary with articles info
        """
        data = {}

        with open(self.__csv_file, 'r') as file:
            reader = csv.DictReader(file, CSVReader.FIELDS)
            for row in reader:
                dir_name = row[CSVReader.FIELD_DIR]
                # Remove first column so it will not  be part of iteration later
                row.pop(CSVReader.FIELD_DIR)
                data[dir_name] = []
                for key in row.keys():
                    if row[key]:
                        data[dir_name].append(row[key])
        return data


class Preservation:

    # Zip file name to download the zip file to temp directory
    ARTICLES_ZIP_NAME = "articles.zip"
    # Identifier file name
    IDENTIFIER_FILE = "identifier.txt"
    # CSV file foor identifiers
    IDENTIFIERS_CSV = "identifiers.csv"
    # Temp directory
    UPLOAD_DIR = app.config.get("UPLOAD_DIR", ".")

    def __init__(self, owner):
        self.__created_time = dates.format(datetime.utcnow(),"%Y-%m-%d-%H-%M-%S")
        self.__dir_name = owner + "-" + self.__created_time
        self.__local_dir = os.path.join(Preservation.UPLOAD_DIR, self.__dir_name)
        self.__preservation_dir = os.path.join(self.__local_dir, self.__dir_name)
        self.__csv_articles_dict = None

    @property
    def dir_name(self):
        return self.__dir_name

    def disk_space_available(self):
        """
        Check if there is enough disk space to save file
        :param file_size:
        :return: True or False
        """
        stats = shutil.disk_usage(Preservation.UPLOAD_DIR)
        # TODO implement storage availability check
        return True

    def create_local_directories(self):
        """
        Create a local directories to download the files and
        to create preservation package
        :param owner: User who upload files
        :return:
        """
        try:
            os.mkdir(self.__local_dir)
            os.mkdir(self.__preservation_dir)
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
        if self.disk_space_available():
            self.create_local_directories()
            file_path = os.path.join(self.__local_dir, Preservation.ARTICLES_ZIP_NAME)
            try:
                file.save(file_path)
            except Exception as e:
                raise PreservationStorageException(message="Could not save file in Temp directory", inner=e)
        else:
            raise PreservationStorageException(message="Not enough disk space to save file")

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

    def create_package_structure(self):
        """ Create preservation package

        Iterates through the sub directories.
        Retrieve article info for each article.
        Creates preservation directories

        :return:
        """
        for dir, subdirs, files in os.walk(self.__local_dir):

            app.logger.debug("Directory : " + dir )
            app.logger.debug("Sub Directories : " + str(subdirs) )
            app.logger.debug("Files : " + str(files) )

            if Preservation.IDENTIFIERS_CSV in files:
                # Get articles info from csv file
                csv_reader = CSVReader(os.path.join(dir, Preservation.IDENTIFIERS_CSV))
                self.__csv_articles_dict = csv_reader.articles_info()
            self.__process_article(dir, files)

    def __process_article(self, dir, files):

        identifiers = None
        dir_name = os.path.basename(dir)

        # check if identifier file exist
        if Preservation.IDENTIFIER_FILE in files:
            with open(os.path.join(dir, Preservation.IDENTIFIER_FILE)) as file:
                identifiers = file.read().splitlines()
        elif self.__csv_articles_dict:
            if dir_name in self.__csv_articles_dict:
                identifiers = self.__csv_articles_dict[dir_name]

        if identifiers:
            article_data = self.get_article(identifiers)

            if article_data:
                issn, article_id, metadata_json = self.get_article_info(article_data)

                package = PreservationPackage()
                package.issn = issn
                package.article_id = article_id
                package.metadata = metadata_json
                package.article_dir = dir
                package.article_files = files
                package.package_dir = self.__preservation_dir

                package.create_article_bagit_structure()


    def get_article(self, identifiers):
        """
        Checks if the identifier is doi or full text
        Pulls article related to the identifier
        :param identifiers:
        :return: article dict
        """
        article = None
        for identifier in identifiers:
            if DOI_COMPILED.match(identifier):
                article = Article.pull_by_key("bibjson.identifier.id", identifier)
            elif HTTP_URL_COMPILED.match(identifier):
                article = Article.pull_by_key("bibjson.link.url", identifier)
            if article:
                return article.data

    def get_article_info(self, article_json):
        """
        Returns article info
        :param article_json:
        :return: issn, article id, metadata json
        """

        metadata_json = self.get_metadata_json(article_json)

        issn = article_json["bibjson"]["journal"]["issns"][0]

        article_id = article_json["id"]

        return issn, article_id, metadata_json

    def get_metadata_json(self, article_json):
        """
        Returns metadata of article which is required for preservation
        :return: metadata
        """
        # Remove unnecessary data
        metadata = deepcopy(article_json)
        metadata.pop("index")
        metadata.pop("admin")
        metadata.pop("es_type")

        return metadata

class PreservationPackage:

    def __init__(self):
        self.issn = None
        self.article_id = None
        self.metadata = None
        self.article_dir = None
        self.article_files = None
        self.package_dir = None

    def create_article_bagit_structure(self):
        """
        Create directory structure for packaging
        Create necessary files
        Create bagit files
        :return:
        """

        journal_dir = os.path.join(self.package_dir, self.issn)
        if not os.path.exists(journal_dir):
            os.mkdir(journal_dir)

        dest_article_dir = os.path.join(journal_dir, self.article_id)
        if not os.path.exists(dest_article_dir):
            # Create article directory
            os.mkdir(dest_article_dir)

            # Create metadata directory
            metada_dir = os.path.join(dest_article_dir, "metadata")
            if not os.path.exists(metada_dir):
                os.mkdir(metada_dir)

            # Copy the files from user uploaded directory to the package
            for file in self.article_files:
                if not file == Preservation.IDENTIFIER_FILE:
                    src = os.path.join(self.article_dir, file)
                    dest = os.path.join(dest_article_dir,file)
                    shutil.copy(src,dest)

            # Create metadata file with article information
            with open(os.path.join(metada_dir, "metadata.json"), 'w+') as metadata_file:
                metadata_file.write(json.dumps(self.metadata, indent=4))

            # Create a tag file with uuid of the article
            with open(os.path.join(metada_dir, "tag.txt"), 'w+') as metadata_file:
                metadata_file.write(json.dumps(self.article_id, indent=4))

        # Bag the article
        bagit.make_bag(dest_article_dir, checksums=["sha256"])


