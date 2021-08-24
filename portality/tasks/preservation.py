import csv
import hashlib
import json
import logging
import os
import requests
import shutil
import tarfile
from bagit import make_bag, BagError
from copy import deepcopy
from datetime import datetime
from zipfile import ZipFile

from portality.background import BackgroundTask, BackgroundApi
from portality.core import app
from portality.decorators import write_required
from portality.lib import dates
from portality.models import Article, BackgroundJob, PreservationState
from portality.regex import DOI_COMPILED, HTTP_URL_COMPILED
from portality.tasks.redis_huey import main_queue, configure


class PreservationException(Exception):
    """~~PreservationException:Exception~~"""
    pass


class PreservationStorageException(Exception):
    pass


class ValidationError(Exception):
    pass


class PreservationBackgroundTask(BackgroundTask):
    """~~PreservationBackground:Feature~~"""

    __action__ = "preserve"

    @classmethod
    def prepare(cls, username, **kwargs):
        """
        ~~->Prepare:Feature~~
        Create necessary directories and save the file.
        Creates the background job
        :param username:
        :param kwargs:
        :return: background job
        """

        created_time = dates.format(datetime.utcnow(), "%Y-%m-%d-%H-%M-%S")
        dir_name = username + "-" + created_time
        local_dir = os.path.join(Preservation.UPLOAD_DIR, dir_name)
        file = kwargs.get("upload_file")

        preservation = Preservation(local_dir)
        preservation.save_file(file)

        # ~~-> BackgroundJob:Feature~~
        # prepare a job record
        job = BackgroundJob()
        job.user = username
        job.action = cls.__action__

        params = {}
        cls.set_param(params, "local_dir", local_dir)
        job.params = params

        return job

    def run(self):

        job = self.background_job

        params = job.params
        local_dir = self.get_param(params, "local_dir")
        model_id = self.get_param(params, "model_id")
        app.logger.debug(f"Local dir {local_dir}")
        app.logger.debug(f"model_id {model_id}")

        preserve_model = PreservationState.pull(model_id)
        preserve_model.background_task_id = job.id
        preserve_model.pending()
        preserve_model.save()

        # ~~-> Preservation:Feature~~
        preserv = Preservation(local_dir)
        try:
            job.add_audit_message("Extract zip file")
            preserv.extract_zip_file()
            app.logger.debug("Extracted zip file")

            job.add_audit_message("Create Package structure")
            preserv.create_package_structure()
            app.logger.debug("Created package structure")

            # ~~-> PreservationPackage:Feature~~
            package = PreservationPackage(preserv.preservation_dir)
            job.add_audit_message("Create preservation package")
            tar_file = package.create_package()
            app.logger.debug(f"Created tar file {tar_file}")

            job.add_audit_message("Create shasum")
            sha256 = package.sha256()

            job.add_audit_message("Upload package")
            response = package.upload_package(sha256)
            app.logger.debug(f"Uploaded. Response{response.text}")

            job.add_audit_message("Validate response")
            self.validate_response(response, tar_file, sha256, preserve_model)

        except (PreservationException, Exception) as exp:
            # ~~-> PreservationException:Exception~~
            preserve_model.failed(str(exp))
            preserve_model.save()
            app.logger.exception("Error at background task")
            raise

    def cleanup(self):
        """~~-> Cleanup:Feature~~
        Cleanup any resources
        :return:
        """
        job = self.background_job
        params = job.params
        local_dir = self.get_param(params, "local_dir")
        Preservation.delete_local_directory(local_dir)

    def validate_response(self, response, tar_file, sha256, model):
        """~~-> ValidateResponse:Feature~~
        Validate the response from server
        :param response: response object
        :param tar_file: tar file name
        :param sha256: sha256sum value
        :param model: model object to update status
        """
        if response.status_code == 200:
            res_json = json.loads(response.text)
            files = res_json["files"]
            # Success response
            # {"files": [{"name": "name_of_tarball.tar.gz",
            #             "sha256": "decafbad"}]}
            if files:
                # Check if the response is type dict or list
                if isinstance(files, dict):
                    res_filename = files["name"]
                    res_shasum = files["sha256"]
                elif isinstance(files, list):
                    if len(files) > 0:
                        res_filename = files[0]["name"]
                        res_shasum = files[0]["sha256"]

                if res_filename and res_filename == tar_file:
                    if res_shasum and res_shasum == sha256:
                        app.logger.info("succesfully uploaded")
                        model.uploaded_to_ia()
                    else:
                        model.failed("shasum in response doesn't match")
                else:
                    model.failed("tar filename in response doesn't match")

            else:
                # Error response
                # {"result": "ERROR","manifest_type": "BagIt",
                #     "manifests": [
                #         {"id": "033168cd016a49eb8c3097d800f1b85f",
                #             "result": "SUCCESS"},
                #         {"id": "00003741594643f4996e2555a01e03c7",
                #             "result": "ERROR",
                #             "errors": [
                #                   "missing_files": [],
                #                   "mismatch_hashes": [{
                #                       "file": "path/to/file",
                #                       "expected": "decafbad",
                #                       "actual": "deadbeaf"}],
                #                   "manifest_parsing_errors": [
                #                   "some weird error"]]}]}
                result = res_json["result"]
                if result and result == "ERROR":
                    error_str = "Upload failed due error at IA server side"
                else:
                    error_str = "Unknown Error: Not a valid response"

                app.logger.error(error_str)
                model.failed(error_str)

            model.save()
        else:
            app.logger.error(f"Upload failed {response.text}")
            model.failed(response.text)
            model.save()


    @classmethod
    def submit(cls, background_job):
        """~~-> SubmitJob:Feature~~
        Submit Background job"""
        background_job.save(blocking=True)
        preserve.schedule(args=(background_job.id,), delay=10)

@main_queue.task(**configure("preserve"))
@write_required(script=True)
def preserve(job_id):
    """~~-> CreateBackgroundTask:Feature"""
    job = BackgroundJob.pull(job_id)
    task = PreservationBackgroundTask(job)
    BackgroundApi.execute(task)



class CSVReader:
    """~~CSVReader:Feature~~"""

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
    """~~Preservation:Feature~~"""

    # Zip file name to download the zip file to temp directory
    ARTICLES_ZIP_NAME = "articles.zip"
    # Identifier file name
    IDENTIFIER_FILE = "identifier.txt"
    # CSV file foor identifiers
    IDENTIFIERS_CSV = "identifiers.csv"
    # Temp directory
    UPLOAD_DIR = app.config.get("UPLOAD_DIR", ".")

    def __init__(self, local_dir):
        self.__dir_name = os.path.basename(local_dir)
        self.__local_dir = os.path.join(local_dir, "tmp")
        self.__preservation_dir = os.path.join(local_dir, self.__dir_name)
        self.__csv_articles_dict = None

    @property
    def dir_name(self):
        return self.__dir_name

    @property
    def preservation_dir(self):
        return self.__preservation_dir

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
        """~~-> CreateDirectories:Feature~~
        Create local directories to download the files and
        to create preservation package
        """
        try:
            os.makedirs(self.__local_dir, exist_ok=True)
            os.makedirs(self.__preservation_dir, exist_ok=True)
        except OSError as exp:
            raise PreservationStorageException("Could not create temp directory")

    @classmethod
    def delete_local_directory(cls, local_dir):
        """~~-> DeleteDirectories:Feature~~
        Deletes the directory
        """
        if os.path.exists(local_dir):
            try:
                shutil.rmtree(local_dir)
            except Exception as e:
                raise PreservationStorageException("Could not delete Temp directory")

    def save_file(self, file):
        """~~-> SaveFile:Feature~~
        Save the file on to local directory
        :param file: File object
        """
        self.create_local_directories()
        file_path = os.path.join(self.__local_dir, Preservation.ARTICLES_ZIP_NAME)
        try:
            file.save(file_path)
        except Exception as e:
            raise PreservationStorageException("Could not save file in Temp directory")


    def extract_zip_file(self):
        """~~-> ExctractZipFile:Feature~~
        Extracts zip file in the Temp directory
        """
        file_path = os.path.join(self.__local_dir, Preservation.ARTICLES_ZIP_NAME)

        if os.path.exists(file_path):
            with ZipFile(file_path, 'r') as zFile:
                zFile.extractall(self.__local_dir)
        else:
            raise PreservationException(f"Could not find zip file at Temp directory {file_path}")

    def create_package_structure(self):
        """ ~~-> CreatePackageStructure:Feature~~
        Create preservation package

        Iterates through the sub directories.
        Retrieve article info for each article.
        Creates preservation directories

        """
        for dir, subdirs, files in os.walk(self.__local_dir):

            app.logger.debug("Directory : " + dir )
            app.logger.debug("Sub Directories : " + str(subdirs) )
            app.logger.debug("Files : " + str(files) )

            if Preservation.IDENTIFIERS_CSV in files:
                # Get articles info from csv file
                # ~~-> CSVReader:Feature~~
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
                try:
                    # ~~-> ArticlePackage:Feature~~
                    package = AtriclePackage()
                    package.issn = issn
                    package.article_id = article_id
                    package.metadata = metadata_json
                    package.article_dir = dir
                    package.article_files = files
                    package.package_dir = self.__preservation_dir

                    package.create_article_bagit_structure()
                except Exception as exp:
                    app.logger.exception(f"Error while create article ( {article_id} ) package")

            else:
                # log and skip the article if not found
                app.logger.error(f"Could not retrieve article for indentifier(s) {identifiers}")



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
            else:
                return None

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

class AtriclePackage:
    """ ~~ArticlePackage:Feature~~"""

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
        Create required additional files
        Create bagit files
        """
        #  Validate if required data is available
        self.validate()

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

            try:
                # Bag the article
                make_bag(dest_article_dir, checksums=["sha256"])
            except BagError as bagError:
                app.logger.excception(f"Error while creating Bag for article {self.article_id}")
                raise PreservationException("Error while creating Bag")

    def validate(self):
        variables_list = []

        if not self.package_dir:
            variables_list.append("package_dir")
        if not self.metadata:
            variables_list.append("metadata")
        if not self.article_dir:
            variables_list.append("article_dir")
        if not self.article_files or len(self.article_files) == 0:
            variables_list.append("article_files")
        if not self.article_id:
            variables_list.append("article_id")
        if not self.issn:
            variables_list.append("issn")

        if len(variables_list) > 0:
            app.logger.debug(f"Validation Values : package_dir {self.package_dir} "
                f"metadata {self.metadata} article_dir {self.article_dir} "
                f"article_files {self.article_files} article_id {self.article_id} issn {self.issn}")
            raise ValidationError(f"Required fields cannot be empty {variables_list}")


class PreservationPackage:
    """~~PreservationPackage:Feature~~
    Creates preservation package and upload to Internet Server
    """

    def __init__(self, directory):
        self.package_dir = directory
        self.tar_file = self.package_dir+".tar.gz"
        self.tar_file_name = os.path.basename(self.tar_file)

    def create_package(self):
        """
        Creates tar file for the package directory
        :return: tar file name
        """
        try:
            with tarfile.open(self.tar_file, "w:gz") as tar:
                tar.add(self.package_dir, arcname=os.path.basename(self.package_dir))
        except Exception as exp:
            app.logger.exception("Error creating tar file")
            raise PreservationException("Error while creating the tar file")

        return self.tar_file_name

    def upload_package(self, sha256sum):

        url = app.config.get("PRESERVATION_URL")
        username = app.config.get("PRESERVATION_USERNAME")
        password = app.config.get("PRESERVATION_PASSWD")
        collection = app.config.get("PRESERVATION_COLLECTION")
        collection_id = app.config.get("PRESERVATION_COLLECTION_ID")

        file_name = os.path.basename(self.tar_file)

        # payload for upload request
        payload = {
            'directories': file_name,
            'org': 'DOAJ',
            'client': 'DOAJ_CLI',
            'username': 'doaj_uploader',
            'size': '',
            'organization': '1',
            'orgname': 'DOAJ',
            'collection': collection_id,
            'collname': collection,
            'sha256sum': sha256sum
        }
        app.logger.info(payload)

        headers = {}
        # get the file to upload
        try:
            with open(self.tar_file, "rb") as f:
                files = {'file_field': (file_name, f)}
                response = requests.post(url, headers=headers, auth=(username, password), files=files, data=payload)
        except (IOError,Exception) as exp:
            app.logger.exception("Error opening the tar file")
            raise PreservationException("Error Uploading tar file to IA server")

        return response

    def sha256(self):
        """
        Creates sha256 hash for the tar file
        """
        sha256_hash = hashlib.sha256()

        with open(self.tar_file, "rb") as f:
            # Read and update hash string value in blocks of 64K
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()