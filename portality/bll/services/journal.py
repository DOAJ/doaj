import csv
import logging
import random
import re
import string
from datetime import datetime
from datetime import timedelta
import os
import shutil
from collections import defaultdict

from portality import lock
from portality import models, constants
from portality.bll import exceptions
from portality.bll.doaj import DOAJ
from portality.core import app
from portality.crosswalks.journal_questions import Journal2QuestionXwalk
from portality.lib import dates
from portality.lib.argvalidate import argvalidate
from portality.lib.dates import FMT_DATETIME_SHORT
from portality.store import StoreException
from portality.store import StoreFactory, StoreException, prune_container
from portality.util import no_op


class JournalService(object):
    """
    ~~Journal:Service~~
    """
    def journal_2_application(self, journal, account=None, keep_editors=False):
        """
        Function to convert a given journal into an application object.

        Provide the journal, and it will be converted
        in-memory to the application object (currently a Suggestion).  The new application
        WILL NOT be saved by this method.

        If an account is provided, this will validate that the account holder is
        allowed to make this conversion

        :param journal: a journal to convert
        :param account: an account doing the action - optional, if specified the application will only be created if the account is allowed to
        :return: Suggestion object
        """

        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("journal_2_application", [
            {"arg": journal, "instance" : models.Journal, "allow_none" : False, "arg_name" : "journal"},
            {"arg" : account, "instance" : models.Account, "arg_name" : "account"}
        ], exceptions.ArgumentException)

        if app.logger.isEnabledFor(logging.DEBUG): app.logger.debug("Entering journal_2_application")

        # ~~-> AuthNZ:Service~~
        authService = DOAJ.authorisationService()

        # if an account is specified, check that it is allowed to perform this action
        if account is not None:
            try:
                authService.can_create_update_request(account, journal)    # throws exception if not allowed
            except exceptions.AuthoriseException as e:
                msg = "Account {x} is not permitted to create an update request on journal {y}".format(x=account.id, y=journal.id)
                app.logger.info(msg)
                e.args += (msg,)
                raise

        # copy all the relevant information from the journal to the application
        bj = journal.bibjson()
        notes = journal.notes

        application = models.Suggestion()   # ~~-> Application:Model~~
        application.set_application_status(constants.APPLICATION_STATUS_UPDATE_REQUEST)
        application.set_current_journal(journal.id)
        if keep_editors is True:
            if journal.editor is not None:
                application.set_editor(journal.editor)
            if journal.editor_group is not None:
                application.set_editor_group(journal.editor_group)
        for n in notes:
            # NOTE: we keep the same id for notes between journal and application, since ids only matter within
            # the scope of a record there are no id clashes, and at the same time it may be useful in future to
            # check the origin of some journal notes by comparing ids to application notes.
            application.add_note_by_dict(n)
        application.set_owner(journal.owner)
        application.set_bibjson(bj)
        application.date_applied = dates.now_str()

        if app.logger.isEnabledFor(logging.DEBUG): app.logger.debug("Completed journal_2_application; return application object")
        return application

    def journal(self, journal_id, lock_journal=False, lock_account=None, lock_timeout=None):
        """
        Function to retrieve a journal by its id, and to optionally lock the resource

        May raise a Locked exception, if a lock is requested but can't be obtained.

        :param journal_id: the id of the journal
        :param: lock_journal: should we lock the resource on retrieval
        :param: lock_account: which account is doing the locking?  Must be present if lock_journal=True
        :param: lock_timeout: how long to lock the resource for.  May be none, in which case it will default
        :return: Tuple of (Journal Object, Lock Object)
        """
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("journal", [
            {"arg": journal_id, "allow_none" : False, "arg_name" : "journal_id"},
            {"arg": lock_journal, "instance" : bool, "allow_none" : False, "arg_name" : "lock_journal"},
            {"arg": lock_account, "instance" : models.Account, "allow_none" : True, "arg_name" : "lock_account"},
            {"arg": lock_timeout, "instance" : int, "allow_none" : True, "arg_name" : "lock_timeout"}
        ], exceptions.ArgumentException)

        # retrieve the journal
        journal = models.Journal.pull(journal_id)

        # if we've retrieved the journal, and a lock is requested, request it
        the_lock = None
        if journal is not None and lock_journal:
            if lock_account is not None:
                # ~~->Lock:Feature~~
                the_lock = lock.lock(constants.LOCK_JOURNAL, journal_id, lock_account.id, lock_timeout)
            else:
                raise exceptions.ArgumentException("If you specify lock_journal on journal retrieval, you must also provide lock_account")

        return journal, the_lock

    def csv(self, prune=True, logger=None, store=None):
        """
        Generate the Journal CSV

        ~~-> JournalCSV:Feature~~

        :param set_cache: whether to update the cache
        :param out_dir: the directory to output the file to.  If set_cache is True, this argument will be overridden by the cache container
        :return: Tuple of (attachment_name, URL)
        """
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("csv", [
            {"arg": prune, "allow_none": False, "arg_name": "prune"},
            {"arg": logger, "allow_none": True, "arg_name": "logger"}
        ], exceptions.ArgumentException)

        # None isn't executable, so convert logger to NO-OP
        if logger is None:
            logger = no_op

        export_start_time = dates.now()

        query = models.JournalQuery().all_in_doaj()

        export_svc = DOAJ.exportService()
        tmp_filepath, tmp_filename = export_svc.csv(models.Journal, query, logger=logger, admin_fieldset=False)

        jc = models.JournalCSV()
        jc.export_date = export_start_time

        if store is None:
            store = StoreFactory.get(constants.STORE__SCOPE__JOURNAL_CSV)

        container = app.config.get("STORE_JOURNAL_CSV_CONTAINER")
        filename = 'doaj_journalcsv_' + dates.format(export_start_time, FMT_DATETIME_SHORT) + '_utf8.csv'
        try:
            store.store(container, filename, source_path=tmp_filepath)
            url = store.url(container, filename)
            logger("Stored CSV in main cache store at {x}".format(x=url))
            jc.set_csv(container, filename, os.path.getsize(tmp_filepath), url)
        except:
            logger("Could not store CSV in main cache store: {x}".format(x=tmp_filename))
            raise StoreException("Could not store CSV in main cache store: {x}".format(x=tmp_filename))

        export_svc.delete_tmp_csv(tmp_filename)
        logger("Deleted file from tmp store")

        jc.save()

        if prune:
            logger("Pruning old CSVs from store")
            self.prune_csvs(store=store, logger=logger)
            logger("Pruned old CSVs from store")

        # update the ES record to point to the new file
        return jc

    def admin_csv(self, file_path, obscure_accounts=True, add_sensitive_account_info=False):
        """
        ~~AdminJournalCSV:Feature->JournalCSV:Feature~~

        :param file_path: where to put the CSV
        :param obscure_accounts: anonymise the account data with consistent random strings
        :param add_sensitive_account_info: augment the CSV with account information - account ID, account name, account email addr
        """
        query = models.JournalQuery().all_in_doaj()

        export_svc = DOAJ.exportService()
        export_svc.csv(models.Journal, query, out_file=file_path,
                            admin_fieldset=True,
                            obscure_accounts=obscure_accounts,
                            add_sensitive_account_info=add_sensitive_account_info
                            )

    def prune_csvs(self, store=None, logger=None):
        if store is None:
            store = StoreFactory.get(constants.STORE__SCOPE__JOURNAL_CSV)

        # None isn't executable, so convert logger to NO-OP
        if logger is None:
            logger = no_op

        # First we're going to remove all the files for csv records which are too old to keep
        total = models.JournalCSV.count()
        old_csvs = models.JournalCSV.all_csvs_before(dates.before_now(app.config.get("NON_PREMIUM_DELAY_SECONDS") + 86400))

        # if removing the old_dds would leave us without any data dump records, then don't do anything
        if total <= len(old_csvs):
            logger("Not removing any old journal csv records, as this would leave us with none")
        else:
            for jc in old_csvs:
                ac = jc.container
                af = jc.filename
                store.delete_file(ac, af)
                jc.delete()

        # Second, we're going to look at all records, and keep only the most recent one from each day
        thin = models.JournalCSV.all_csvs_before(dates.before_now(86400))

        def separate_by_newest_per_day(jcs):
            # Group objects by their day
            grouped_by_day = defaultdict(list)
            for jc in jcs:
                day = dates.parse(jc.export_day)  # Extract the day (ignoring time)
                grouped_by_day[day].append(jc)

            newest_per_day = []
            everything_else = []

            # Find the newest object for each day
            for day, items in grouped_by_day.items():
                items.sort(key=lambda x: x.export_date, reverse=True)  # Sort by date descending
                newest_per_day.append(items[0])  # Add the newest object
                everything_else.extend(items[1:])  # Add the rest to "everything else"

            return newest_per_day, everything_else

        # Separate the objects into newest_per_day and everything_else
        newest_per_day, everything_else = separate_by_newest_per_day(thin)
        for jc in everything_else:
            ac = jc.container
            af = jc.filename
            store.delete_file(ac, af)
            jc.delete()

        # Third we're going to check the container for files which don't have index records, and
        # clean them up

        # get the files in storage
        container = app.config.get("STORE_JOURNAL_CSV_CONTAINER")
        container_files = store.list(container)

        # if the filename doesn't match anything, remove the file
        for cf in container_files:
            jc = models.JournalCSV.find_by_filename(cf)
            if jc is None or len(jc) == 0:
                logger("No related index record; Deleting file {x} from storage container {y}".format(x=cf, y=container))
                store.delete_file(container, cf)

        # Finally, we check all the records in the index and confirm their files exist, and if not
        # remove the record
        for jc in models.JournalCSV.iterate_unstable():
            missing = False
            if jc.container is not None and jc.filename is not None:
                if jc.filename not in store.list(jc.container):
                    logger("File {x} in container {y} does not exist".format(x=jc.filename, y=jc.container))
                    missing = True

            if missing:
                logger("File missing for {x}".format(x=jc.id))
                jc.delete()

    def get_premium_csv(self):
        # Get the latest data dump
        return models.JournalCSV.find_latest()

    def get_free_csv(self, cutoff=None):
        if cutoff is None:
            cutoff = dates.before_now(app.config.get("NON_PREMIUM_DELAY_SECONDS") + 86400)

        # get the first dump after the cutoff
        option = models.JournalCSV.first_csv_after(cutoff=cutoff)
        if option is not None:
            return option

        # if there was no such dump, just return the latest
        return models.JournalCSV.find_latest()

    def get_temporary_url(self, jc: models.JournalCSV):
        container = jc.container
        filename = jc.filename

        if container is None or filename is None:
            raise exceptions.NoSuchPropertyException("Cannot find container and filename for journal csv")

        main_store = StoreFactory.get(constants.STORE__SCOPE__JOURNAL_CSV)
        store_url = main_store.temporary_url(container, filename,
                                             timeout=app.config.get("JOURNAL_CSV_URL_TIMEOUT", 3600))
        return store_url