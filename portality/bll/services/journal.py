import csv
import logging
import random
import re
import string
from datetime import datetime
from datetime import timedelta
import os
import shutil

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
from portality.store import StoreFactory, prune_container
from portality.ui.messages import Messages
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

    def find(self, identifier):
        if len(identifier) == 9:
            # search both in doaj and withdrawn to know whether to return 404 (not found) or 410 (gone)
            js = models.Journal.find_by_issn(identifier)
            if len(js) == 0:
                return None

            # if there is one or more, try to get the active one
            active_journals = [j for j in js if j.is_in_doaj()]
            if len(active_journals) > 1:
                raise exceptions.TooManyJournals(Messages.TOO_MANY_JOURNALS.format(identifier=identifier))

            return active_journals[0] if len(active_journals) == 1 else None

        elif len(identifier) == 32:
            # Pull by ES identifier
            j = models.Journal.pull(identifier)  # Returns None on fail
            if j is None:
                return None

            if j.is_in_doaj() is False:
                raise exceptions.JournalWithdrawn
            return j

        return None

    def csv(self, prune=True, logger=None):
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

        query = models.JournalQuery().all_in_doaj()

        export_svc = DOAJ.exportService()
        tmp_filepath, tmp_filename = export_svc.csv(models.Journal, query, logger=logger, admin_fieldset=False)

        # ~~->FileStore:Feature~~
        filename = 'journalcsv__doaj_' + dates.now_str(FMT_DATETIME_SHORT) + '_utf8.csv'
        container_id = app.config.get("STORE_CACHE_CONTAINER")
        mainStore = StoreFactory.get("cache")
        try:
            mainStore.store(container_id, filename, source_path=tmp_filepath)
            url = mainStore.url(container_id, filename)
            logger("Stored CSV in main cache store at {x}".format(x=url))
        finally:
            export_svc.delete_tmp_csv(tmp_filename)
            logger("Deleted file from tmp store")

        action_register = []
        if prune:
            logger("Pruning old CSVs from store")

            def sort(filelist):
                rx = "journalcsv__doaj_(.+?)_utf8.csv"
                return sorted(filelist, key=lambda x: datetime.strptime(re.match(rx, x).groups(1)[0], FMT_DATETIME_SHORT), reverse=True)

            def _filter(f_name):
                return f_name.startswith("journalcsv__")

            action_register = prune_container(mainStore, container_id, sort, filter=_filter, keep=2, logger=logger)
            logger("Pruned old CSVs from store")

        # update the ES record to point to the new file
        # ~~-> Cache:Model~~
        models.Cache.cache_csv(url)
        logger("Stored CSV URL in ES Cache")
        return url, action_register

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
