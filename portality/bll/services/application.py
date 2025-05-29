import csv
import json
import logging
import re
from io import StringIO

from portality import constants, lock, models
from portality.bll import DOAJ, exceptions
from portality.core import app
from portality.crosswalks.journal_form import JournalFormXWalk
from portality.crosswalks.journal_questions import Journal2PublisherUploadQuestionsXwalk, QuestionTransformError
from portality.forms.application_forms import ApplicationFormFactory
from portality.lib import dates, httputil
from portality.lib.argvalidate import argvalidate
from portality.ui.messages import Messages


class ApplicationService(object):
    """
    ~~Application:Service->DOAJ:Service~~
    """

    def auto_assign_ur_editor_group(self, ur: models.Application):
        """
        Auto assign editor group to the update request
        :param ur:
        :return:
        """
        if not app.config.get("AUTO_ASSIGN_UR_EDITOR_GROUP", False):
            return ur

        target = None
        reason = ""

        by_owner = models.URReviewRoute.by_account(ur.owner)
        if by_owner is not None:
            reason = Messages.AUTOASSIGN__OWNER_MAPPED.format(owner=ur.owner, target=by_owner.target)
            target = by_owner.target

        if target is None:
            by_country = models.URReviewRoute.by_country_name(ur.bibjson().country_name())
            if by_country is not None:
                reason = Messages.AUTOASSIGN__COUNTRY_MAPPED.format(country=ur.bibjson().country_name(), target=by_country.target)
                target = by_country.target

        if target is None:
            return ur

        id = models.EditorGroup.group_exists_by_name(target)
        if id is None:
            ur.add_note(Messages.AUTOASSIGN__NOTE__EDITOR_GROUP_MISSING.format(target=target))
            return ur

        ur.set_editor_group(target)
        ur.remove_editor()
        ur.add_note(Messages.AUTOASSIGN__NOTE__ASSIGN.format(target=target, reason=reason))
        return ur

    @classmethod
    def retrieve_ur_editor_group_sheets(cls, prune=True):
        start = dates.now()

        publisher_sheet = app.config.get("AUTO_ASSIGN_EDITOR_BY_PUBLISHER_SHEET")
        country_sheet = app.config.get("AUTO_ASSIGN_EDITOR_BY_COUNTRY_SHEET")

        presp = httputil.get(publisher_sheet)
        if presp.status_code != 200:
            raise exceptions.RemoteServiceException("Failed to retrieve publisher sheet from {x}".format(x=publisher_sheet))

        cresp = httputil.get(country_sheet)
        if cresp.status_code != 200:
            raise exceptions.RemoteServiceException("Failed to retrieve country sheet from {x}".format(x=country_sheet))

        presp.encoding = "utf-8"
        pdata = presp.text
        if pdata is None or pdata == "":
            raise ValueError("Publisher sheet is empty at {x}".format(x=publisher_sheet))

        cresp.encoding = "utf-8"
        cdata = cresp.text
        if cdata is None or cdata == "":
            raise ValueError("Country sheet is empty at {x}".format(x=country_sheet))

        preader = csv.reader(StringIO(pdata))
        creader = csv.reader(StringIO(cdata))

        preader.__next__()
        creader.__next__()

        routers = []

        for i, row in enumerate(preader):
            account = row[1]
            group = row[2]

            if account is None or account == "":
                raise ValueError(f"Publisher Sheet: Account is empty on row {i+2}")
            if group is None or group == "":
                raise ValueError(f"Publisher Sheet: Group is empty on row {i+2}")

            acc = models.Account.pull(account)
            if acc is None:
                raise ValueError(f"Publisher Sheet: Account {account} not found in DOAJ; row {i+2}")
            if models.EditorGroup.group_exists_by_name(group) is None:
                raise ValueError(f"Publisher Sheet: Group {group} not found in DOAJ; row {i+2}")

            router = models.URReviewRoute()
            router.account_id = acc.id
            router.target = group
            routers.append(router)

        for i, row in enumerate(creader):
            country = row[0]
            group = row[1]

            if country is None or country == "":
                raise ValueError(f"Country Sheet: Country is empty on row {i+2}")
            if group is None or group == "":
                raise ValueError(f"Country Sheet: Group is empty on row {i+2}")

            if models.EditorGroup.group_exists_by_name(group) is None:
                raise ValueError(f"Country Sheet: Group {group} not found in DOAJ; row {i+2}")

            router = models.URReviewRoute()
            router.country = country
            router.target = group
            routers.append(router)

        # if we get to here we have two valid sheets, so we can update
        # the local copy
        # Note that we HAVE to block this save, as if the records are not
        # guaranteed saved before the prune starts all the old records will remain, and
        # they can mess with the auto-assignment logic
        models.URReviewRoute.save_all(routers, blocking=True)

        if prune:
            cls.prune_ur_review_routes(cutoff=start)

        return routers

    @classmethod
    def prune_ur_review_routes(cls, cutoff=None):
        """
        Prune the URReviewRoute records older than cutoff
        :param cutoff:
        :return:
        """
        if cutoff is None:
            cutoff = dates.now() - dates.timedelta(days=1)

        q = {
            "query": {
                "range": {
                    "created_date": {
                        "lt": dates.format(cutoff)
                    }
                }
            }
        }

        total = models.URReviewRoute.count()
        candidates = models.URReviewRoute.count(q)
        if candidates == 0 or total <= candidates:
            return 0

        models.URReviewRoute.delete_by_query(q)
        return candidates


    @staticmethod
    def prevent_concurrent_ur_submission(ur: models.Application, record_if_not_concurrent=True):
        """
        Prevent duplicated update request submission
        :param ur:
        :param record_if_not_concurrent:
        :return:
        """
        cs = DOAJ.concurrencyPreventionService()

        if ur.current_journal is not None and ur.id is not None:
            if cs.check_concurrency(ur.current_journal, ur.id):
                raise exceptions.ConcurrentUpdateRequestException(Messages.CONCURRENT_UPDATE_REQUEST)

            if record_if_not_concurrent:
                cs.store_concurrency(ur.current_journal, ur.id, timeout=app.config.get("UR_CONCURRENCY_TIMEOUT", 10))

    def reject_application(self, application, account, provenance=True, note=None, manual_update=True):
        """
        Reject an application.  This will:
        * set the application status to "rejected" (if not already)
        * remove the current_journal field, and move it to related_journal (if needed)
        * remove the current_application field from the related journal (if needed)
        * save the application
        * write a provenance record for the rejection (if requested)

        :param application:
        :param account:
        :param provenance:
        :param note:
        :param manual_update:
        :return:
        """
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("reject_application", [
            {"arg": application, "instance" : models.Application, "allow_none" : False, "arg_name" : "application"},
            {"arg" : account, "instance" : models.Account, "allow_none" : False, "arg_name" : "account"},
            {"arg" : provenance, "instance" : bool, "allow_none" : False, "arg_name" : "provenance"},
            {"arg" : note, "instance" : str, "allow_none" : True, "arg_name" : "note"},
            {"arg" : manual_update, "instance" : bool, "allow_none" : False, "arg_name" : "manual_update"}
        ], exceptions.ArgumentException)

        if app.logger.isEnabledFor(logging.DEBUG): app.logger.debug("Entering reject_application")

        # ~~->Journal:Service~~
        journalService = DOAJ.journalService()

        # check we're allowed to carry out this action
        if not account.has_role("reject_application"):
            raise exceptions.AuthoriseException(message="This user is not allowed to reject applications", reason=exceptions.AuthoriseException.WRONG_ROLE)

        # ensure the application status is "rejected"
        if application.application_status != constants.APPLICATION_STATUS_REJECTED:
            application.set_application_status(constants.APPLICATION_STATUS_REJECTED)

        # add the note to the application
        if note is not None:
            application.add_note(note)

         # retrieve the id of the current journal if there is one
        cj_id = application.current_journal
        cj = None

        # if there is a current_journal record, remove it, and record
        # it as a related journal.  This will let us come back later and know
        # which journal record this was intended as an update against if needed.
        if cj_id is not None:
            cj, _ = journalService.journal(cj_id)
            application.remove_current_journal()
            if cj is not None:
                application.set_related_journal(cj_id)
                cj.remove_current_application()

        # if there is a current journal, we will have modified it above, so save it
        if cj is not None:
            saved = cj.save()
            if saved is None:
                raise exceptions.SaveException("Save on current_journal in reject_application failed")

        # if we were asked to record this as a manual update, record that on the application
        if manual_update:
            application.set_last_manual_update()

        saved = application.save()
        if saved is None:
            raise exceptions.SaveException("Save on application in reject_application failed")

        # record a provenance record that this action took place
        if provenance:
            # ~~->Provenance:Model~~
            models.Provenance.make(account, constants.PROVENANCE_STATUS_REJECTED, application)

        if app.logger.isEnabledFor(logging.DEBUG): app.logger.debug("Completed reject_application")


    def unreject_application(self,
                             application: models.Application,
                             account: models.Account,
                             manual_update: bool = True,
                             disallow_status: list = None):
        """
        Un-reject an application.  This will:
        * check that the application status is no longer "rejected" (throw an error if it is)
        * check for a related journal, and if one is present, promote that to current_journal (if no other UR exists)
        * save the application

        :param application:
        :param account:
        :param manual_update:
        :param disallow_status: statuses that we are not allowed to unreject to (excluding rejected, which is always disallowed)
        :return:
        """
        if app.logger.isEnabledFor(logging.DEBUG): app.logger.debug("Entering unreject_application")

        if application is None:
            raise exceptions.ArgumentException(Messages.BLL__UNREJECT_APPLICATION__NO_APPLICATION)

        if account is None:
            raise exceptions.ArgumentException(Messages.BLL__UNREJECT_APPLICATION__NO_ACCOUNT)

        # check we're allowed to carry out this action
        if not account.has_role("unreject_application"):
            raise exceptions.AuthoriseException(message=Messages.BLL__UNREJECT_APPLICATION__WRONG_ROLE,
                                                reason=exceptions.AuthoriseException.WRONG_ROLE)

        # ensure the application status is not "rejected"
        if application.application_status == constants.APPLICATION_STATUS_REJECTED:
            raise exceptions.IllegalStatusException(message=Messages.BLL__UNREJECT_APPLICATION__ILLEGAL_STATE_REJECTED.format(id=application.id))

        # by default reject transitions to the accepted status (because acceptance implies other processing that this
        # method does not handle).  You can override this by passing in an empty list
        if disallow_status is None:
            disallow_status = [constants.APPLICATION_STATUS_ACCEPTED]
        if application.application_status in disallow_status:
            raise exceptions.IllegalStatusException(
                message=Messages.BLL__UNREJECT_APPLICATION__ILLEGAL_STATE_DISALLOWED.format(
                    id=application.id, x=application.application_status
                ))

        rjid = application.related_journal
        if rjid:
            ur = models.Application.find_latest_by_current_journal(rjid)
            if ur:
                raise exceptions.DuplicateUpdateRequest(message=Messages.BLL__UNREJECT_APPLICATION__DUPLICATE_UR.format(
                    id=application.id,
                    urid=ur.id,
                    jid=rjid
                ))

            rj = models.Journal.pull(rjid)
            if rj is None:
                raise exceptions.NoSuchObjectException(Messages.BLL__UNREJECT_APPLICATION__JOURNAL_MISSING.format(
                    jid=rjid, id=application.id
                ))

            # update the application's view of the current journal
            application.set_current_journal(rjid)
            application.remove_related_journal()

            # update the journal's view of the current application
            rj.set_current_application(application.id)
            rj.remove_related_application(application.id)

            saved = rj.save()
            if saved is None:
                raise exceptions.SaveException(Messages.BLL__UNREJECT_APPLICATION__SAVE_FAIL.format(
                    obj="current_journal",
                    id=rj.id
                ))

            # if we were asked to record this as a manual update, record that on the application
            if manual_update:
                application.set_last_manual_update()

            saved = application.save()
            if saved is None:
                raise exceptions.SaveException(Messages.BLL__UNREJECT_APPLICATION__SAVE_FAIL.format(
                    obj="application",
                    id=application.id
                ))

        if app.logger.isEnabledFor(logging.DEBUG): app.logger.debug("Completed unreject_application")


    def accept_application(self, application, account, manual_update=True, provenance=True, save_journal=True, save_application=True):
        """
        Take the given application and create the Journal object in DOAJ for it.

        The account provided must have permission to create journals from applications.

        :param application: The application to be converted
        :param account: The account doing the conversion
        :param manual_update: Whether to record this update as a manual update on both the application and journal objects
        :param provenance: Whether to write provenance records for this operation
        :param save_journal: Whether to save the journal that is produced
        :param save_application: Whether to save the application after it has been modified
        :return: The journal that was created
        """
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("accept_application", [
            {"arg": application, "instance" : models.Suggestion, "allow_none" : False, "arg_name" : "application"},
            {"arg" : account, "instance" : models.Account, "allow_none" : False, "arg_name" : "account"},
            {"arg" : manual_update, "instance" : bool, "allow_none" : False, "arg_name" : "manual_update"},
            {"arg" : provenance, "instance" : bool, "allow_none" : False, "arg_name" : "provenance"},
            {"arg" : save_journal, "instance" : bool, "allow_none" : False, "arg_name" : "save_journal"},
            {"arg" : save_application, "instance" : bool, "allow_none" : False, "arg_name" : "save_application"}
        ], exceptions.ArgumentException)

        if app.logger.isEnabledFor(logging.DEBUG): app.logger.debug("Entering accept_application")

        # ensure that the account holder has a suitable role
        if not account.has_role("accept_application"):
            raise exceptions.AuthoriseException(
                message="User {x} is not permitted to accept application {y}".format(x=account.id, y=application.id),
                reason=exceptions.AuthoriseException.WRONG_ROLE)

        # ensure the application status is "accepted"
        if application.application_status != constants.APPLICATION_STATUS_ACCEPTED:
            application.set_application_status(constants.APPLICATION_STATUS_ACCEPTED)

        # make the resulting journal (and save it if requested)
        j = self.application_2_journal(application, manual_update=manual_update)
        if save_journal is True:
            saved = j.save()
            if saved is None:
                raise exceptions.SaveException("Save of resulting journal in accept_application failed")

        # retrieve the id of the current journal if there is one
        cj = application.current_journal

        # if there is a current_journal record, remove it
        if cj is not None:
            application.remove_current_journal()

        # set the relationship with the journal
        application.set_related_journal(j.id)

        # if we were asked to record this as a manual update, record that on the application
        # (the journal is done implicitly above)
        if manual_update:
            application.set_last_manual_update()

        if provenance:
            # record the event in the provenance tracker
            models.Provenance.make(account, constants.PROVENANCE_STATUS_ACCEPTED, application)

        # save the application if requested
        if save_application is True:
            application.save()

        if app.logger.isEnabledFor(logging.DEBUG): app.logger.debug("Completed accept_application")

        return j

    def reject_update_request_of_journal(self, journal_id, account):
        """
            Rejects update request associated with journal

            :param journal_id:
            :param account:
            :return: Journal object
        """
        ur = models.Application.find_latest_by_current_journal(journal_id)  # ~~->Application:Model~~
        if ur:
            self.reject_application(ur, account, note=Messages.AUTOMATICALLY_REJECTED_UPDATE_REQUEST_NOTE)
            return ur
        else:
            return None

    def reject_update_request_of_journals(self, ids, account):
        """
            Rejects update request associated with journal

            :param ids:
            :param account:
            :return: Journal object
        """
        ur_ids = []
        for journal_id in ids:
            ur = self.reject_update_request_of_journal(journal_id, account)
            if ur:
                ur_ids.append(ur.id)
        return ur_ids

    def update_request_for_journal(self, journal_id, account=None, lock_timeout=None, lock_records=True):
        """
        Obtain an update request application object for the journal with the given journal_id

        An update request may either be loaded from the database, if it already exists, or created
        in-memory if it has not previously been created.

        If an account is provided, this will validate that the account holder is allowed to make
        the conversion from journal to application, if a conversion is required.

        When this request runs, the journal will be locked to the provided account if an account is
        given.  If the application is loaded from the database, this will also be locked for the account
        holder.

        :param journal_id:
        :param account:
        :return: a tuple of (Application Object, Journal Lock, Application Lock)
        """
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("update_request_for_journal", [
            {"arg": journal_id, "instance" : str, "allow_none" : False, "arg_name" : "journal_id"},
            {"arg" : account, "instance" : models.Account, "allow_none" : True, "arg_name" : "account"},
            {"arg" : lock_timeout, "instance" : int, "allow_none" : True, "arg_name" : "lock_timeout"}
        ], exceptions.ArgumentException)

        if app.logger.isEnabledFor(logging.DEBUG): app.logger.debug("Entering update_request_for_journal")

        # ~~-> Journal:Service~~
        # ~~-> AuthNZ:Service~~
        journalService = DOAJ.journalService()
        authService = DOAJ.authorisationService()

        # first retrieve the journal, and return empty if there isn't one.
        # We don't attempt to obtain a lock at this stage, as we want to check that the user is authorised first
        journal_lock = None
        journal, _ = journalService.journal(journal_id)
        if journal is None:
            app.logger.info("Request for journal {x} did not find anything in the database".format(x=journal_id))
            return None, None, None

        # if the journal is not in_doaj, we won't create an update request for it
        if not journal.is_in_doaj():
            app.logger.info("Request for journal {x} found it is not in_doaj; will not create update request".format(x=journal_id))
            return None, None, None

        # retrieve the latest application attached to this journal
        application_lock = None
        application = models.Suggestion.find_latest_by_current_journal(journal_id)  # ~~->Application:Model~~

        # if no such application exists, create one in memory (this will check that the user is permitted to create one)
        # at the same time, create the lock for the journal.  This will throw an AuthorisedException or a Locked exception
        # (in that order of preference) if any problems arise.
        if application is None:
            app.logger.info("No existing update request for journal {x}; creating one".format(x=journal.id))
            application = journalService.journal_2_application(journal, account=account)
            application.set_is_update_request(True)
            if account is not None:
                if lock_records:
                    journal_lock = lock.lock("journal", journal_id, account.id)

        # otherwise check that the user (if given) has the rights to edit the application
        # then lock the application and journal to the account.
        # If a lock cannot be obtained, unlock the journal and application before we return
        elif account is not None:
            try:
                authService.can_edit_application(account, application)
                if lock_records:
                    application_lock = lock.lock("suggestion", application.id, account.id)
                    journal_lock = lock.lock("journal", journal_id, account.id)
            except lock.Locked as e:
                if application_lock is not None: application_lock.delete()
                if journal_lock is not None: journal_lock.delete()
                raise
            except exceptions.AuthoriseException as e:
                msg = "Account {x} is not permitted to edit the current update request on journal {y}".format(x=account.id, y=journal.id)
                app.logger.info(msg)
                e.args += (msg,)
                raise

            app.logger.info("Using existing application {y} as update request for journal {x}".format(y=application.id, x=journal.id))

        if app.logger.isEnabledFor(logging.DEBUG): app.logger.debug("Completed update_request_for_journal; return application object")

        return application, journal_lock, application_lock

    def application_2_journal(self, application, manual_update=True):
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("application_2_journal", [
            {"arg": application, "instance" : models.Suggestion, "allow_none" : False, "arg_name" : "application"},
            {"arg" : manual_update, "instance" : bool, "allow_none" : False, "arg_name" : "manual_update"}
        ], exceptions.ArgumentException)

        if app.logger.isEnabledFor(logging.DEBUG): app.logger.debug("Entering application_2_journal")

        # create a new blank journal record, which we can build up
        journal = models.Journal()  # ~~->Journal:Model~~

        # first thing is to copy the bibjson as-is wholesale,
        abj = application.bibjson()
        journal.set_bibjson(abj)
        jbj = journal.bibjson()

        # now carry over key administrative properties from the application itself
        # * notes
        # * editor
        # * editor_group
        # * owner
        notes = application.notes

        if application.editor is not None:
            journal.set_editor(application.editor)
        if application.editor_group is not None:
            journal.set_editor_group(application.editor_group)
        for note in notes:
            journal.add_note_by_dict(note)
        if application.owner is not None:
            journal.set_owner(application.owner)

        b = application.bibjson()
        if b.pissn == "":
            b.add_identifier("pissn", None)
        if b.eissn == "":
            b.add_identifier("eissn", None)

        # no relate the journal to the application and place it in_doaj
        journal.add_related_application(application.id, dates.now_str())
        journal.set_in_doaj(True)

        # if we've been called in the context of a manual update, record that
        if manual_update:
            journal.set_last_manual_update()

        # if this is an update to an existing journal, then we can also port information from
        # that journal
        if application.current_journal is not None:
            cj = models.Journal.pull(application.current_journal)
            if cj is not None:
                # carry the id and the created date
                journal.set_id(cj.id)
                journal.set_created(cj.created_date)

                # bring forward any notes from the old journal record
                old_notes = cj.notes
                for note in old_notes:
                    journal.add_note_by_dict(note)

                # bring forward any related applications
                related = cj.related_applications
                for r in related:
                    journal.add_related_application(r.get("application_id"), r.get("date_accepted"), r.get("status"))

                # carry over any properties that are not already set from the application
                # * editor & editor_group (together or not at all)
                # * owner
                if journal.editor is None and journal.editor_group is None:
                    journal.set_editor(cj.editor)
                    journal.set_editor_group(cj.editor_group)
                if journal.owner is None:
                    journal.set_owner(cj.owner)

        if app.logger.isEnabledFor(logging.DEBUG): app.logger.debug("Completing application_2_journal")

        return journal

    def application(self, application_id, lock_application=False, lock_account=None, lock_timeout=None):
        """
        Function to retrieve an application by its id

        :param application_id: the id of the application
        :param: lock_application: should we lock the resource on retrieval
        :param: lock_account: which account is doing the locking?  Must be present if lock_journal=True
        :param: lock_timeout: how long to lock the resource for.  May be none, in which case it will default
        :return: Tuple of (Suggestion Object, Lock Object)
        """
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("application", [
            {"arg": application_id, "allow_none" : False, "arg_name" : "application_id"},
            {"arg": lock_application, "instance" : bool, "allow_none" : False, "arg_name" : "lock_journal"},
            {"arg": lock_account, "instance" : models.Account, "allow_none" : True, "arg_name" : "lock_account"},
            {"arg": lock_timeout, "instance" : int, "allow_none" : True, "arg_name" : "lock_timeout"}
        ], exceptions.ArgumentException)

        # pull the application from the database
        application = models.Suggestion.pull(application_id)

        # if we've retrieved the journal, and a lock is requested, request it
        the_lock = None
        if application is not None and lock_application:
            if lock_account is not None:
                # ~~->Lock:Feature~~
                the_lock = lock.lock(constants.LOCK_APPLICATION, application_id, lock_account.id, lock_timeout)
            else:
                raise exceptions.ArgumentException("If you specify lock_application on application retrieval, you must also provide lock_account")

        return application, the_lock

    def delete_application(self, application_id, account):
        """
        Function to delete an application, and all references to it in other objects (current and related journals)

        The application and all related journals need to be locked before this process can proceed, so you may get a
        lock.Locked exception

        :param application_id:
        :param account:
        :return:
        """
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("delete_application", [
            {"arg": application_id, "instance" : str, "allow_none" : False, "arg_name" : "application_id"},
            {"arg" : account, "instance" : models.Account, "allow_none" : False, "arg_name" : "account"}
        ], exceptions.ArgumentException)

        # ~~-> Journal:Service~~
        # ~~-> AuthNZ:Service~~
        journalService = DOAJ.journalService()
        authService = DOAJ.authorisationService()

        # get hold of a copy of the application.  If there isn't one, our work here is done
        # (note the application could be locked, in which case this will raise a lock.Locked exception)

        # get the application
        application, _ = self.application(application_id)
        if application is None:
            raise exceptions.NoSuchObjectException

        # determine if the user can edit the application
        authService.can_edit_application(account, application)

        # attempt to lock the record (this may raise a Locked exception)
        # ~~-> Lock:Feature~~
        alock = lock.lock(constants.LOCK_APPLICATION, application_id, account.id)

        # obtain the current journal, with associated lock
        current_journal = None
        cjlock = None
        if application.current_journal is not None:
            try:
                current_journal, cjlock = journalService.journal(application.current_journal, lock_journal=True, lock_account=account)
            except lock.Locked as e:
                # if the resource is locked, we have to back out
                if alock is not None: alock.delete()
                raise

        # obtain the related journal, with associated lock
        related_journal = None
        rjlock = None
        if application.related_journal is not None:
            try:
                related_journal, rjlock = journalService.journal(application.related_journal, lock_journal=True, lock_account=account)
            except lock.Locked:
                # if the resource is locked, we have to back out
                if alock is not None: alock.delete()
                if cjlock is not None: cjlock.delete()
                raise

        try:
            if current_journal is not None:
                current_journal.remove_current_application()
                saved = current_journal.save()
                if saved is None:
                    raise exceptions.SaveException("Unable to save journal record")

            if related_journal is not None:
                relation_record = related_journal.related_application_record(application_id)
                if relation_record is None:
                    relation_record = {}
                related_journal.add_related_application(application_id, relation_record.get("date_accepted"), "deleted")
                saved = related_journal.save()
                if saved is None:
                    raise exceptions.SaveException("Unable to save journal record")

            application.delete()

        finally:
            if alock is not None: alock.delete()
            if cjlock is not None: cjlock.delete()
            if rjlock is not None: rjlock.delete()

        return

    def validate_update_csv(self, file_path, account: models.Account):
        # Open with encoding that deals with the Byte Order Mark since we're given files from Windows.
        with open(file_path, "r", encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            validation = CSVValidationReport()

            # verify header row with current CSV headers, report errors
            header_row = reader.fieldnames
            allowed_headers = Journal2PublisherUploadQuestionsXwalk.question_list()
            lower_case_allowed_headers = list(map(str.lower, allowed_headers))
            required_headers = Journal2PublisherUploadQuestionsXwalk.required_questions()

            # Always perform a match check on supplied headers, not counting order
            for i, h in enumerate(header_row):
                if h and h not in allowed_headers:
                    if h.lower() in lower_case_allowed_headers:
                        expected = allowed_headers[lower_case_allowed_headers.index(h.lower())]
                        validation.header(validation.WARN, i, Messages.JOURNAL_CSV_VALIDATE__HEADER_CASE_MISMATCH.format(h=h, expected=expected))
                    else:
                        validation.header(validation.ERROR, i, Messages.JOURNAL_CSV_VALIDATE__INVALID_HEADER.format(h=h))

            missing_required = False
            for rh in required_headers:
                if rh not in header_row:
                    validation.general(validation.ERROR, Messages.JOURNAL_CSV_VALIDATE__REQUIRED_HEADER_MISSING.format(h=rh))
                    missing_required = True
            if missing_required:
                return validation

            # Talking about spreadsheets, so we start at 1
            row_ix = 1

            # ~~ ->$JournalUpdateByCSV:Feature ~~
            for row in reader:
                row_ix += 1
                validation.log(f'Processing CSV row {row_ix}')

                # Skip empty rows
                if not any(row.values()):
                    validation.log("Skipping empty row {x}.".format(x=row_ix))
                    continue

                # Pull by ISSNs
                issns = [
                    row.get(Journal2PublisherUploadQuestionsXwalk.q("pissn")),
                    row.get(Journal2PublisherUploadQuestionsXwalk.q("eissn"))
                ]
                issns = [issn for issn in issns if issn is not None and issn != ""]

                try:
                    j = models.Journal.find_by_issn(issns, in_doaj=True, max=1).pop(0)
                except IndexError:
                    validation.row(validation.ERROR, row_ix, Messages.JOURNAL_CSV_VALIDATE__MISSING_JOURNAL.format(issns=", ".join(issns)))
                    continue

                # Confirm that the account is allowed to update the journal (is admin or owner)
                if not account.is_super and account.id != j.owner:
                    validation.row(validation.ERROR, row_ix, Messages.JOURNAL_CSV_VALIDATE__OWNER_MISMATCH.format(acc=account.id, issns=", ".join(issns)))
                    continue

                # By this point the issns are confirmed as matching a journal that belongs to the publisher
                validation.log('Validating update for journal with ID ' + j.id)

                # Load remaining rows into application form as an update
                # ~~ ^->JournalQuestions:Crosswalk ~~
                journal_form = JournalFormXWalk.obj2form(j)
                journal_questions = Journal2PublisherUploadQuestionsXwalk.journal2question(j)

                try:
                    update_form, updates = Journal2PublisherUploadQuestionsXwalk.question2form(j, row)
                except QuestionTransformError as e:
                    question = Journal2PublisherUploadQuestionsXwalk.q(e.key)
                    journal_value = [y for x, y in journal_questions if x == question][0]
                    validation.value(validation.ERROR, row_ix, header_row.index(question),
                                     Messages.JOURNAL_CSV_VALIDATE__INVALID_DATA.format(question=question),
                                     was=journal_value, now=e.value)
                    continue

                if len(updates) == 0:
                    validation.row(validation.WARN, row_ix, Messages.JOURNAL_CSV_VALIDATE__NO_DATA_CHANGE)
                    continue

                # if we get to here, then there are updates
                [validation.log(upd) for upd in updates]

                # If a field is disabled in the UR Form Context, then we must confirm that the form data from the
                # file has not changed from that provided in the source
                formulaic_context = ApplicationFormFactory.context("update_request")
                disabled_fields = formulaic_context.disabled_fields()
                trip_wire = False
                for field in disabled_fields:
                    field_name = field.get("name")
                    question = Journal2PublisherUploadQuestionsXwalk.q(field_name)
                    update_value = update_form.get(field_name)
                    journal_value = journal_form.get(field_name)
                    if update_value != journal_value:
                        trip_wire = True
                        validation.value(validation.ERROR, row_ix, header_row.index(question),
                                         Messages.JOURNAL_CSV_VALIDATE__QUESTION_CANNOT_CHANGE.format(question=question),
                                         was=journal_value, now=update_value)

                if trip_wire:
                    continue

                # Create an update request for this journal
                update_req = None
                jlock = None
                alock = None
                try:
                    # ~~ ^->UpdateRequest:Feature ~~
                    update_req, jlock, alock = self.update_request_for_journal(j.id, account=account, lock_records=False)
                except exceptions.AuthoriseException as e:
                    validation.row(validation.ERROR, row_ix, Messages.JOURNAL_CSV_VALIDATE__CANNOT_MAKE_UR.format(reason=e.reason))
                    continue

                # If we don't have a UR, we can't continue
                if update_req is None:
                    validation.row(validation.ERROR, row_ix, Messages.JOURNAL_CSV_VALIDATE__MISSING_JOURNAL.format(issns=", ".join(issns)))
                    continue

                # validate update_form - portality.forms.application_processors.PublisherUpdateRequest
                # ~~ ^->UpdateRequest:FormContext ~~
                fc = formulaic_context.processor(
                    formdata=update_form,
                    source=update_req
                )

                if not fc.validate():
                    for k, v in fc.form.errors.items():
                        question = Journal2PublisherUploadQuestionsXwalk.q(k)
                        try:
                            pos = header_row.index(question)
                        except ValueError:
                            # this is because the validation is on a field which is not in the csv, so it must
                            # be due to an existing validation error in the data, and not something the publisher
                            # can do anything about
                            continue
                        now = row.get(question)
                        was = [v for q, v in journal_questions if q == question][0]
                        if isinstance(v[0], dict):
                            for sk, sv in v[0].items():
                                validation.value(validation.ERROR, row_ix, pos, ". ".join([str(x) for x in sv]),
                                             was=was, now=now)
                        elif isinstance(v[0], list):
                            # If we have a list, we must go a level deeper
                            validation.value(validation.ERROR, row_ix, pos, ". ".join([str(x) for x in v[0]]),
                                             was=was, now=now)
                        else:
                            validation.value(validation.ERROR, row_ix, pos, ". ".join([str(x) for x in v]),
                                             was=was, now=now)

        return validation


class CSVValidationReport:

    WARN = "warn"
    ERROR = "error"

    CLEANR = re.compile('<.*?>')

    def __init__(self):
        self._general = []
        self._headers = {}
        self._row = {}
        self._values = {}
        self._log = []
        self._errors = False
        self._warnings = False

    @property
    def general_errors(self):
        return self._general

    @property
    def header_errors(self):
        return self._headers

    @property
    def row_errors(self):
        return self._row

    @property
    def value_errors(self):
        return self._values

    def has_errors_or_warnings(self):
        return self._errors or self._warnings

    def has_errors(self):
        return self._errors

    def has_warnings(self):
        return self._warnings

    def record_error_type(self, error_type):
        if error_type == self.WARN:
            self._warnings = True
        elif error_type == self.ERROR:
            self._errors = True

    def general(self, error_type, msg):
        msg = self._cleanhtml(msg)
        self.log("[" + error_type + "] " + msg)
        self._general.append((error_type, msg))
        self.record_error_type(error_type)

    def header(self, error_type, pos, msg):
        msg = self._cleanhtml(msg)
        self.log("[" + error_type + "] " + msg)
        self._headers[pos] = (error_type, msg)
        self.record_error_type(error_type)

    def row(self, error_type, row, msg):
        msg = self._cleanhtml(msg)
        self.log("[" + error_type + "] " + msg)
        self._row[row] = (error_type, msg)
        self.record_error_type(error_type)

    def value(self, error_type, row, pos, msg, was, now):
        msg = self._cleanhtml(msg)
        if row not in self._values:
            self._values[row] = {}
        self.log("[" + error_type + "] " + msg)
        self._values[row][pos] = (error_type, msg, was, now)
        self.record_error_type(error_type)

    def log(self, msg):
        msg = self._cleanhtml(msg)
        self._log.append(msg)

    def _cleanhtml(self, raw_html):
        cleantext = re.sub(self.CLEANR, '', raw_html)
        return cleantext

    def json(self, indent=None):
        _repr = {
            "has_errors": self._errors,
            "has_warnings": self._warnings,
            "general": self._general,
            "headers": self._headers,
            "rows": self._row,
            "values": self._values,
            "log": self._log
        }
        return json.dumps(_repr, indent=indent)
