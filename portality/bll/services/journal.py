import logging

from portality.lib.argvalidate import argvalidate
from portality.lib import dates
from portality import models, constants
from portality.bll import exceptions
from portality.core import app
from portality import lock
from portality.bll.doaj import DOAJ
from portality.store import StoreFactory, prune_container
from portality.crosswalks.journal_questions import Journal2QuestionXwalk

from datetime import datetime
import re, csv, random, string


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
            application.add_note(n.get("note"), n.get("date"), n.get("id"))
        application.set_owner(journal.owner)
        application.set_seal(journal.has_seal())
        application.set_bibjson(bj)
        application.date_applied = dates.now()

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

    def csv(self, prune=True):
        """
        Generate the Journal CSV

        ~~-> JournalCSV:Feature~~

        :param set_cache: whether to update the cache
        :param out_dir: the directory to output the file to.  If set_cache is True, this argument will be overridden by the cache container
        :return: Tuple of (attachment_name, URL)
        """
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("csv", [
            {"arg": prune, "allow_none" : False, "arg_name" : "prune"}
        ], exceptions.ArgumentException)

        # ~~->FileStoreTemp:Feature~~
        filename = 'journalcsv__doaj_' + datetime.strftime(datetime.utcnow(), '%Y%m%d_%H%M') + '_utf8.csv'
        container_id = app.config.get("STORE_CACHE_CONTAINER")
        tmpStore = StoreFactory.tmp()
        out = tmpStore.path(container_id, filename, create_container=True, must_exist=False)

        with open(out, 'w', encoding='utf-8') as csvfile:
            self._make_journals_csv(csvfile)

        # ~~->FileStore:Feature~~
        mainStore = StoreFactory.get("cache")
        try:
            mainStore.store(container_id, filename, source_path=out)
            url = mainStore.url(container_id, filename)
        finally:
            tmpStore.delete_file(container_id, filename) # don't delete the container, just in case someone else is writing to it

        action_register = []
        if prune:
            def sort(filelist):
                rx = "journalcsv__doaj_(.+?)_utf8.csv"
                return sorted(filelist, key=lambda x: datetime.strptime(re.match(rx, x).groups(1)[0], '%Y%m%d_%H%M'), reverse=True)

            def _filter(f_name):
                return f_name.startswith("journalcsv__")
            action_register = prune_container(mainStore, container_id, sort, filter=_filter, keep=2)

        # update the ES record to point to the new file
        # ~~-> Cache:Model~~
        models.Cache.cache_csv(url)
        return url, action_register

    def admin_csv(self, file_path, account_sub_length=8, obscure_accounts=True):
        """
        ~~AdminJournalCSV:Feature->JournalCSV:Feature~~

        :param file_path:
        :param account_sub_length:
        :param obscure_accounts:
        :return:
        """
        # create a closure for substituting owners for consistently used random strings
        unmap = {}

        def usernames(j):
            o = j.owner
            if obscure_accounts:
                if o in unmap:
                    sub = unmap[o]
                else:
                    sub = "".join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for i in range(account_sub_length))
                    unmap[o] = sub
                return [("Owner", sub)]
            else:
                return [("Owner", o)]

        with open(file_path, "w", encoding="utf-8") as f:
            self._make_journals_csv(f, [usernames])

    @staticmethod
    def _make_journals_csv(file_object, additional_columns=None):
        """
        Make a CSV file of information for all journals.
        :param file_object: a utf8 encoded file object.
        """
        YES_NO = {True: 'Yes', False: 'No', None: '', '': ''}

        def _get_doaj_meta_kvs(journal):
            """
            Get key, value pairs for some meta information we want from the journal object
            :param journal: a models.Journal
            :return: a list of (key, value) tuples for our metadata
            """
            kvs = [
                ("Subjects", ' | '.join(journal.bibjson().lcc_paths())),
                ("DOAJ Seal", YES_NO.get(journal.has_seal(), "")),
                # ("Tick: Accepted after March 2014", YES_NO.get(journal.is_ticked(), "")),
                ("Added on Date", journal.created_date),
                ("Last updated Date", journal.last_manual_update)
            ]
            return kvs

        def _get_doaj_toc_kv(journal):
            return "URL in DOAJ", app.config.get('JOURNAL_TOC_URL_FRAG', 'https://doaj.org/toc/') + journal.id

        def _get_article_kvs(journal):
            stats = journal.article_stats()
            kvs = [
                ("Number of Article Records", str(stats.get("total"))),
                ("Most Recent Article Added", stats.get("latest"))
            ]
            return kvs

        # ~~!JournalCSV:Feature->Journal:Model~~
        cols = {}
        for j in models.Journal.all_in_doaj(page_size=1000):     #Fixme: limited by ES, this may not be sufficient
            bj = j.bibjson()
            issn = bj.get_one_identifier(idtype=bj.P_ISSN)
            if issn is None:
                issn = bj.get_one_identifier(idtype=bj.E_ISSN)
            if issn is None:
                continue

            # ~~!JournalCSV:Feature->JournalQuestions:Crosswalk~~
            kvs = Journal2QuestionXwalk.journal2question(j)
            meta_kvs = _get_doaj_meta_kvs(j)
            article_kvs = _get_article_kvs(j)
            additionals = []
            if additional_columns is not None:
                for col in additional_columns:
                    additionals += col(j)
            cols[issn] = kvs + meta_kvs + article_kvs + additionals

            # Get the toc URL separately from the meta kvs because it needs to be inserted earlier in the CSV
            # ~~-> ToC:WebRoute~~
            toc_kv = _get_doaj_toc_kv(j)
            cols[issn].insert(2, toc_kv)

        issns = cols.keys()

        csvwriter = csv.writer(file_object)
        qs = None
        for i in sorted(issns):
            if qs is None:
                qs = [q for q, _ in cols[i]]
                csvwriter.writerow(qs)
            vs = [v for _, v in cols[i]]
            csvwriter.writerow(vs)

    @staticmethod
    def exist_status(journal_id=None, journal=None):
        return JournalExistStatus(journal_id=journal_id, journal=journal)


class JournalExistStatus:
    def __init__(self, journal_id=None, journal=None):
        if journal_id is not None:
            journal = models.Journal.pull(journal_id)
        self.journal = journal

    def is_deleted(self):
        return self.journal is None

    def is_withdrawn(self):
        return self.journal and not self.journal.is_in_doaj()
