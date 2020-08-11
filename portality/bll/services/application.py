import logging

from portality.lib.argvalidate import argvalidate
from portality.lib import dates
from portality import models
from portality.bll import exceptions
from portality.core import app
from portality import constants
from portality import lock
from portality.bll.doaj import DOAJ

class ApplicationService(object):

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
            models.Provenance.make(account, constants.PROVENANCE_STATUS_REJECTED, application)

        if app.logger.isEnabledFor(logging.DEBUG): app.logger.debug("Completed reject_application")

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

    def update_request_for_journal(self, journal_id, account=None, lock_timeout=None):
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
        application = models.Suggestion.find_latest_by_current_journal(journal_id)

        # if no such application exists, create one in memory (this will check that the user is permitted to create one)
        # at the same time, create the lock for the journal.  This will throw an AuthorisedException or a Locked exception
        # (in that order of preference) if any problems arise.
        if application is None:
            app.logger.info("No existing update request for journal {x}; creating one".format(x=journal.id))
            application = journalService.journal_2_application(journal, account=account)
            if account is not None:
                journal_lock = lock.lock("journal", journal_id, account.id)

        # otherwise check that the user (if given) has the rights to edit the application
        # then lock the application and journal to the account.
        # If a lock cannot be obtained, unlock the journal and application before we return
        elif account is not None:
            try:
                authService.can_edit_application(account, application)
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
        journal = models.Journal()

        # first thing is to copy the bibjson as-is wholesale,
        abj = application.bibjson()
        journal.set_bibjson(abj)
        jbj = journal.bibjson()

        # now carry over key administrative properties from the application itself
        # * contacts
        # * notes
        # * editor
        # * editor_group
        # * owner
        # * seal
        # contacts = application.contacts()
        notes = application.notes

        #for contact in contacts:
        #    journal.add_contact(contact.get("name"), contact.get("email"))
        if application.editor is not None:
            journal.set_editor(application.editor)
        if application.editor_group is not None:
            journal.set_editor_group(application.editor_group)
        for note in notes:
            journal.add_note(note.get("note"), note.get("date"), note.get("id"))
        if application.owner is not None:
            journal.set_owner(application.owner)
        journal.set_seal(application.has_seal())

        # no relate the journal to the application and place it in_doaj
        journal.add_related_application(application.id, dates.now())
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
                    journal.add_note(note.get("note"), note.get("date"), note.get("id"))

                # bring forward any related applications
                related = cj.related_applications
                for r in related:
                    journal.add_related_application(r.get("application_id"), r.get("date_accepted"), r.get("status"))

                # carry over any properties that are not already set from the application
                # * contact
                # * editor & editor_group (together or not at all)
                # * owner
                #if len(journal.contacts()) == 0:
                #    old_contacts = cj.contacts()
                #    for contact in old_contacts:
                #        journal.add_contact(contact.get("name"), contact.get("email"))
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
            except lock.Locked as e:
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
