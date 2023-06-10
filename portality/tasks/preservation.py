import csv
import hashlib
import json
import os
import shutil
import tarfile
from copy import deepcopy
from datetime import datetime
from zipfile import ZipFile

import requests
from bagit import make_bag, BagError

from portality.background import BackgroundTask, BackgroundApi
from portality.bll import DOAJ
from portality.core import app
from portality.lib import dates
from portality.models import Account, Article, BackgroundJob, PreservationState
from portality.regex import DOI_COMPILED, HTTP_URL_COMPILED
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import main_queue


class PreservationException(Exception):
    """~~PreservationException:Exception~~"""
    pass


class PreservationStorageException(Exception):
    pass


class ValidationError(Exception):
    pass


class ArticlePackage:
    """ ~~ArticlePackage:Feature~~"""

    def __init__(self, article_dir, files):
        self.issn = None
        self.article_id = None
        self.metadata = None
        self.article_dir = article_dir
        self.article_files = files
        self.package_dir = None
        self.has_error = False
        self.error_details = None

    def create_article_bagit_structure(self):
        """ ~~-> BagIt:Library~~
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
                    dest = os.path.join(dest_article_dir, file)
                    shutil.copy(src, dest)

            # Create metadata file with article information
            with open(os.path.join(metada_dir, "metadata.json"), 'w+') as metadata_file:
                metadata_file.write(json.dumps(self.metadata, indent=4))

            # Create a identifier file with uuid of the article
            with open(os.path.join(metada_dir, "identifier.txt"), 'w+') as metadata_file:
                metadata_file.write(self.article_id)

            try:
                # Bag the article
                make_bag(dest_article_dir, checksums=["sha256"])
            except BagError:
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


class ArticlesList:
    """This class contains different types of lists depending on the article state"""

    def __init__(self):
        self.__successful_articles = []
        self.__unowned_articles = []
        self.__no_identifier_articles = []
        self.__unbagged_articles = []
        self.__not_found_articles = []
        self.__no_files_articles = []
        self.has_errors = False

    def add_successful_article(self, article: ArticlePackage):
        self.__successful_articles.append(os.path.basename(article.article_dir))

    def add_unowned_articles(self, article: ArticlePackage):
        self.has_errors = True
        self.__unowned_articles.append(os.path.basename(article.article_dir))

    def add_no_identifier_articles(self, article: ArticlePackage):
        self.has_errors = True
        self.__no_identifier_articles.append(os.path.basename(article.article_dir))

    def add_unbagged_articles(self, article: ArticlePackage):
        self.has_errors = True
        self.__unbagged_articles.append(os.path.basename(article.article_dir))

    def add_not_found_articles(self, article: ArticlePackage):
        self.has_errors = True
        self.__not_found_articles.append(os.path.basename(article.article_dir))

    def add_no_files_articles(self, article: ArticlePackage):
        self.__no_files_articles.append(os.path.basename(article.article_dir))

    def successful_articles(self):
        return self.__successful_articles

    def unowned_articles(self):
        return self.__unowned_articles

    def no_identifier_articles(self):
        return self.__no_identifier_articles

    def unbagged_articles(self):
        return self.__unbagged_articles

    def not_found_articles(self):
        return self.__not_found_articles

    def no_files_articles(self):
        return self.__no_files_articles

    def get_count(self):
        return len(self.__successful_articles) + \
               len(self.__unowned_articles) + \
               len(self.__no_identifier_articles) + \
               len(self.__unbagged_articles) + \
               len(self.__not_found_articles) + \
               len(self.__no_files_articles)

    def is_partial_success(self):
        if len(self.__successful_articles) > 0 and \
                (len(self.__unbagged_articles) > 0 or
                 len(self.__unowned_articles) > 0 or
                 len(self.__not_found_articles) > 0 or
                 len(self.__no_identifier_articles) > 0 or
                 len(self.__no_files_articles)):
            return True

        return False


class PreservationBackgroundTask(BackgroundTask):
    """~~PreservationBackground:Feature~~"""

    __action__ = "preserve"

    @classmethod
    def prepare(cls, username, **kwargs):
        """
        Create necessary directories and save the file.
        Creates the background job
        :param username:
        :param kwargs:
        :return: background job
        """

        created_time = dates.now_str("%Y-%m-%d-%H-%M-%S")
        dir_name = username + "-" + created_time
        local_dir = os.path.join(Preservation.UPLOAD_DIR, dir_name)
        file = kwargs.get("upload_file")

        preservation = Preservation(local_dir, username)
        preservation.save_file(file)

        # prepare a job record
        params = {}
        cls.set_param(params, "local_dir", local_dir)
        job = background_helper.create_job(username, cls.__action__,
                                           queue_id=huey_helper.queue_id, params=params)
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
        preserv = Preservation(local_dir, job.user)
        preserv.upload_filename = preserve_model.filename
        try:
            job.add_audit_message("Extract zip file")
            preserv.extract_zip_file()
            app.logger.debug("Extracted zip file")

            job.add_audit_message("Create Package structure")
            articles_list = preserv.create_package_structure()
            self.save_articles_list(articles_list, preserve_model)
            app.logger.debug("Created package structure")

            if len(articles_list.successful_articles()) > 0:
                package = PreservationPackage(preserv.preservation_dir, job.user)
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

                # Check if the only few articles are successful
                if articles_list.is_partial_success():
                    preserve_model.partial()
                    preserve_model.save()
            else:
                # If no previous errors found, check other failure reasons
                if not preserve_model.error:
                    # Check if any articles available
                    if articles_list.get_count() == 0:
                        preserve_model.failed(FailedReasons.no_article_found)
                        preserve_model.save()
                    # All the articles available are invalid
                    else:
                        preserve_model.failed(FailedReasons.no_valid_article_available)
                        preserve_model.save()

        except (PreservationException, Exception) as exp:
            # ~~-> PreservationException:Exception~~
            preserve_model.failed(str(exp))
            preserve_model.save()
            app.logger.exception("Error at background task")
            raise

    def save_articles_list(self, articles_list: ArticlesList, model: PreservationState):
        """
        Saves articles info to the model
        :param articles_list: articles list
        :param model: model object
        """
        if len(articles_list.successful_articles()) > 0:
            model.successful_articles(articles_list.successful_articles())
        if len(articles_list.not_found_articles()) > 0:
            model.not_found_articles(articles_list.not_found_articles())
        if len(articles_list.no_identifier_articles()) > 0:
            model.no_identifier_articles(articles_list.no_identifier_articles())
            if len(articles_list.no_identifier_articles()) == articles_list.get_count():
                model.failed(FailedReasons.no_identifier)
        if len(articles_list.unowned_articles()) > 0:
            model.unowned_articles(articles_list.unowned_articles())
        if len(articles_list.unbagged_articles()) > 0:
            model.unbagged_articles(articles_list.unbagged_articles())
        if len(articles_list.no_files_articles()) > 0:
            model.no_files_articles(articles_list.no_files_articles())
        model.save()

    def cleanup(self):
        """
        Cleanup any resources
        :return:
        """
        job = self.background_job
        params = job.params
        local_dir = self.get_param(params, "local_dir")
        Preservation.delete_local_directory(local_dir)

    def validate_response(self, response, tar_file, sha256, model):
        """
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
                res_filename = None
                res_shasum = None
                if isinstance(files, dict):
                    res_filename = files["name"]
                    res_shasum = files["sha256"]
                elif isinstance(files, list):
                    if len(files) > 0:
                        res_filename = files[0]["name"]
                        res_shasum = files[0]["sha256"]

                if res_filename and res_filename == tar_file:
                    if res_shasum and res_shasum == sha256:
                        app.logger.info("successfully uploaded")
                        model.uploaded_to_ia()
                    else:
                        model.failed(FailedReasons.checksum_doesnot_match)
                else:
                    model.failed(FailedReasons.tar_filename_doesnot_match)

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
                    error_str = FailedReasons.error_response
                else:
                    error_str = FailedReasons.unknown_error_response

                app.logger.error(error_str)
                model.failed(error_str)

            model.save()
        else:
            app.logger.error(f"Upload failed {response.text}")
            model.failed(response.text)
            model.save()

    @classmethod
    def submit(cls, background_job):
        """
        Submit Background job"""
        background_job.save(blocking=True)
        preserve.schedule(args=(background_job.id,), delay=10)


huey_helper = PreservationBackgroundTask.create_huey_helper(main_queue)


@huey_helper.register_execute(is_load_config=True)
def preserve(job_id):
    """~~-> PreservationBackgroundTask:Queue"""
    job = BackgroundJob.pull(job_id)
    task = PreservationBackgroundTask(job)
    BackgroundApi.execute(task)


class CSVReader:
    """~~CSVReader:Feature~~"""

    # column names for csv file.
    # Given more identifiers just to handle any mistakes by user like empty identifiers
    # Max expected identifier are 2 (Full Text URL, DOI) in any order
    FIELD_DIR = "dir_name"
    FIELDS = (FIELD_DIR, "id_1", "id_2", "id_3", "id_4")

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

        with open(self.__csv_file, mode='r', encoding='utf-8-sig') as file:
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
    # CSV file for identifiers
    IDENTIFIERS_CSV = "identifiers.csv"
    # Temp directory
    UPLOAD_DIR = app.config.get("UPLOAD_DIR", ".")

    def __init__(self, local_dir, owner):
        self.__dir_name = os.path.basename(local_dir)
        self.__local_dir = os.path.join(local_dir, "tmp")
        self.__preservation_dir = os.path.join(local_dir, self.__dir_name)
        self.__csv_articles_dict = None
        self.__owner = owner
        self.upload_filename = None

    @property
    def dir_name(self):
        return self.__dir_name

    @property
    def preservation_dir(self):
        return self.__preservation_dir

    def create_local_directories(self):
        """
        Create local directories to download the files and
        to create preservation package
        """
        try:
            os.makedirs(self.__local_dir, exist_ok=True)
            os.makedirs(self.__preservation_dir, exist_ok=True)
        except OSError:
            raise PreservationStorageException("Could not create temp directory")

    @classmethod
    def delete_local_directory(cls, local_dir):
        """
        Deletes the directory
        """
        if os.path.exists(local_dir):
            try:
                shutil.rmtree(local_dir)
            except Exception:
                raise PreservationStorageException("Could not delete Temp directory")

    def save_file(self, file):
        """
        Save the file on to local directory
        :param file: File object
        """
        self.create_local_directories()
        file_path = os.path.join(self.__local_dir, Preservation.ARTICLES_ZIP_NAME)
        try:
            file.save(file_path)
        except Exception:
            raise PreservationStorageException("Could not save file in Temp directory")

    def extract_zip_file(self):
        """
        Extracts zip file in the Temp directory
        """
        file_path = os.path.join(self.__local_dir, Preservation.ARTICLES_ZIP_NAME)

        if os.path.exists(file_path):
            with ZipFile(file_path, 'r') as zFile:
                zFile.extractall(self.__local_dir)
        else:
            raise PreservationException(f"Could not find zip file at Temp directory {file_path}")

    def create_package_structure(self) -> ArticlesList:
        """
        Create preservation package

        Iterates through the sub directories.
        Retrieve article info for each article.
        Creates preservation directories

        """
        articles_list = ArticlesList()

        for dir, subdirs, files in os.walk(self.__local_dir):

            if dir == self.__local_dir:
                continue

            app.logger.debug("Directory : " + dir)
            app.logger.debug("Sub Directories : " + str(subdirs))
            app.logger.debug("Files : " + str(files))

            # Fetch identifiers at the root directory
            if os.path.dirname(dir) == self.__local_dir:
                if Preservation.IDENTIFIERS_CSV in files:
                    # Get articles info from csv file
                    # ~~-> CSVReader:Feature~~
                    csv_reader = CSVReader(os.path.join(dir, Preservation.IDENTIFIERS_CSV))
                    self.__csv_articles_dict = csv_reader.articles_info()
            # process only the directories that has articles
            else:
                self.__process_article(dir, files, articles_list)

        return articles_list

    def __process_article(self, dir_path, files, articles_list):

        identifiers = None
        dir_name = os.path.basename(dir_path)
        package = ArticlePackage(dir_path, files)

        if not os.path.dirname(dir_path) == self.__local_dir:
            if not self.__has_article_files(files):
                articles_list.add_no_files_articles(package)
                return

        # check if identifier file exist
        if Preservation.IDENTIFIER_FILE in files:
            with open(os.path.join(dir_path, Preservation.IDENTIFIER_FILE)) as file:
                identifiers = file.read().splitlines()
        elif self.__csv_articles_dict:
            if dir_name in self.__csv_articles_dict:
                identifiers = self.__csv_articles_dict[dir_name]

        if identifiers:
            article = self.get_article(identifiers)

            if article:
                article_data = article.data

                if not self.owner_of_article(article):
                    articles_list.add_unowned_articles(package)

                else:
                    issn, article_id, metadata_json = self.get_article_info(article_data)
                    try:
                        package = ArticlePackage(dir_path, files)
                        package.issn = issn
                        package.article_id = article_id
                        package.metadata = metadata_json
                        package.package_dir = self.__preservation_dir

                        package.create_article_bagit_structure()

                        articles_list.add_successful_article(package)
                    except Exception:
                        articles_list.add_unbagged_articles(package)
                        app.logger.exception(f"Error while create article ( {article_id} ) package")

            else:
                # skip the article if not found
                app.logger.error(f"Could not retrieve article for identifier(s) {identifiers}")
                articles_list.add_not_found_articles(package)

        else:
            # did not find any identifier for article
            articles_list.add_no_identifier_articles(package)

    def __has_article_files(self, files):
        """
        Checks if any article files available
        :param files:
        :return: True if files available otherwise returns False
        """
        no_of_files = len(files)
        if Preservation.IDENTIFIER_FILE in files:
            if no_of_files > 1:
                return True
            else:
                return False
        else:
            if no_of_files > 0:
                return True
            else:
                return False

    def owner_of_article(self, article):
        """
        Checks if the article is owned by the user
        :param article:
        :return:
        """
        articleService = DOAJ.articleService()
        account = Account.pull(self.__owner)
        is_owner = articleService.has_permissions(account, article, True)
        return is_owner

    def get_article(self, identifiers):
        """
        Checks if the identifier is doi or full text
        Pulls article related to the identifier
        :param identifiers:
        :return: article
        """
        article = None
        for identifier in identifiers:
            if DOI_COMPILED.match(identifier):
                article = Article.pull_by_key("bibjson.identifier.id", identifier)
            elif HTTP_URL_COMPILED.match(identifier):
                article = Article.pull_by_key("bibjson.link.url", identifier)
            if article:
                return article
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


class PreservationPackage:
    """~~PreservationPackage:Feature~~
    Creates preservation package and upload to Internet Server
    """

    def __init__(self, directory, owner):
        self.package_dir = directory
        self.tar_file = self.package_dir + ".tar.gz"
        self.tar_file_name = os.path.basename(self.tar_file)
        self.__owner = owner

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
        collection_dict = app.config.get("PRESERVATION_COLLECTION")
        params = collection_dict[self.__owner]
        collection = params[0]
        collection_id = params[1]

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
        except (IOError, Exception) as exp:
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


class FailedReasons:
    no_identifier = "no_identifier"
    unknown = "unknown"
    checksum_doesnot_match = "checksum_doesnot_match"
    no_article_found = "no_article_found"
    no_valid_article_available = "no_valid_article_available"
    tar_filename_doesnot_match = "response_tar_filename_doesnot_match"
    error_response = "error_response"
    unknown_error_response = "unknown_error_response"
    collection_not_available = "collection_not_available"
