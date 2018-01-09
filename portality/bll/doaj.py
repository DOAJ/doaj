from portality.core import app
from portality.lib.argvalidate import argvalidate
from portality.lib import dates

from portality import models
from portality.formcontext import formcontext
from portality import lock

from portality.bll import exceptions, constants

from werkzeug.datastructures import MultiDict

class DOAJ(object):

    FORMCONTEXT_FACTORIES = {
        "application" : formcontext.ApplicationFormFactory
    }

    def reject_application(self, application, account, provenance=True):
        """
        Reject an application.  This will:
        * set the application status to "rejected" (if not already)
        * remove the current_journal field, and move it to related_journal (if needed)
        * save the application
        * write a provenance record for the rejection (if requested)

        :param application:
        :param account:
        :param provenance:
        :return:
        """
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("reject_application", [
            {"arg": application, "instance" : models.Suggestion, "allow_none" : False, "arg_name" : "application"},
            {"arg" : account, "instance" : models.Account, "allow_none" : False, "arg_name" : "account"},
            {"arg" : provenance, "instance" : bool, "allow_none" : False, "arg_name" : "provenance"}
        ], exceptions.ArgumentException)

        if app.logger.isEnabledFor("debug"): app.logger.debug("Entering reject_application")

        # check we're allowed to carry out this action
        if not account.has_role("reject_application"):
            raise exceptions.AuthoriseException(message="This user is not allowed to reject applications", reason=exceptions.AuthoriseException.WRONG_ROLE)

        # ensure the application status is "rejected"
        if application.application_status != constants.APPLICATION_STATUS_REJECTED:
            application.set_application_status(constants.APPLICATION_STATUS_REJECTED)

        # retrieve the id of the current journal if there is one
        cj = application.current_journal

        # if there is a current_journal record, remove it, and record
        # it as a related journal.  This will let us come back later and know
        # which journal record this was intended as an update against if needed.
        if cj is not None:
            application.remove_current_journal()
            application.set_related_journal(cj)

        saved = application.save()
        if saved is None:
            raise exceptions.SaveException("Save on application in reject_application failed")

        # record a provenance record that this action took place
        if provenance:
            models.Provenance.make(account, constants.PROVENANCE_STATUS_REJECTED, application)

        if app.logger.isEnabledFor("debug"): app.logger.debug("Completed reject_application")

    def accept_application(self, application, account, manual_update=True, provenance=True):
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("accept_application", [
            {"arg": application, "instance" : models.Suggestion, "allow_none" : False, "arg_name" : "application"},
            {"arg" : account, "instance" : models.Account, "allow_none" : False, "arg_name" : "account"},
            {"arg" : manual_update, "instance" : bool, "allow_none" : False, "arg_name" : "manual_update"},
            {"arg" : provenance, "instance" : bool, "allow_none" : False, "arg_name" : "provenance"}
        ], exceptions.ArgumentException)

        if app.logger.isEnabledFor("debug"): app.logger.debug("Entering accept_application")

        # ensure that the account holder has a suitable role
        if not account.has_role("accept_application"):
            raise exceptions.AuthoriseException(
                message="User {x} is not permitted to accept application {y}".format(x=account.id, y=application.id),
                reason=exceptions.AuthoriseException.WRONG_ROLE)

        # ensure the application status is "accepted"
        if application.application_status != constants.APPLICATION_STATUS_ACCEPTED:
            application.set_application_status(constants.APPLICATION_STATUS_ACCEPTED)

        # make the resulting journal
        j = self.application_2_journal(application, manual_update=manual_update)
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

        if app.logger.isEnabledFor("debug"): app.logger.debug("Completed accept_application")

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
            {"arg": journal_id, "instance" : basestring, "allow_none" : False, "arg_name" : "journal_id"},
            {"arg" : account, "instance" : models.Account, "allow_none" : True, "arg_name" : "account"},
            {"arg" : lock_timeout, "instance" : int, "allow_none" : True, "arg_name" : "lock_timeout"}
        ], exceptions.ArgumentException)

        if app.logger.isEnabledFor("debug"): app.logger.debug("Entering update_request_for_journal")

        # first retrieve the journal, and return empty if there isn't one.
        # We don't attempt to obtain a lock at this stage, as we want to check that the user is authorised first
        journal_lock = None
        journal, _ = self.journal(journal_id)
        if journal is None:
            app.logger.info("Request for journal {x} did not find anything in the database".format(x=journal_id))
            return None, None, None

        # retrieve the latest application attached to this journal

        application_lock = None
        application = models.Suggestion.find_latest_by_current_journal(journal_id)

        # if no such application exists, create one in memory (this will check that the user is permitted to create one)
        # at the same time, create the lock for the journal.  This will throw an AuthorisedException or a Locked exception
        # (in that order of preference) if any problems arise.
        if application is None:
            app.logger.info("No existing update request for journal {x}; creating one".format(x=journal.id))
            application = self.journal_2_application(journal, account=account)
            if account is not None:
                journal_lock = lock.lock("journal", journal_id, account.id)

        # otherwise check that the user (if given) has the rights to edit the application
        # then lock the application and journal to the account.
        # If a lock cannot be obtained, unlock the journal and application before we return
        elif account is not None:
            try:
                self.can_edit_update_request(account, application)
                application_lock = lock.lock("suggestion", application.id, account.id)
                journal_lock = lock.lock("journal", journal_id, account.id)
            except lock.Locked as e:
                if application_lock is not None: application_lock.delete()
                if journal_lock is not None: journal_lock.delete()
                raise
            except exceptions.AuthoriseException as e:
                msg = "Account {x} is not permitted to edit the current update request on journal {y}".format(x=account.id, y=journal.id)
                app.logger.info(msg)
                e.message = msg
                raise

            app.logger.info("Using existing application {y} as update request for journal {x}".format(y=application.id, x=journal.id))

        if app.logger.isEnabledFor("debug"): app.logger.debug("Completed update_request_for_journal; return application object")

        return application, journal_lock, application_lock

    def application_2_journal(self, application, manual_update=True):
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("application_2_journal", [
            {"arg": application, "instance" : models.Suggestion, "allow_none" : False, "arg_name" : "application"},
            {"arg" : manual_update, "instance" : bool, "allow_none" : False, "arg_name" : "manual_update"}
        ], exceptions.ArgumentException)

        if app.logger.isEnabledFor("debug"): app.logger.debug("Entering application_2_journal")

        abj = application.bibjson()
        journal = models.Journal()
        journal.set_bibjson(abj)
        jbj = journal.bibjson()
        jbj.active = True

        contacts = application.contacts()
        notes = application.notes

        for contact in contacts:
            journal.add_contact(contact.get("name"), contact.get("email"))
        if application.editor is not None:
            journal.set_editor(application.editor)
        if application.editor_group is not None:
            journal.set_editor_group(application.editor_group)
        for note in notes:
            journal.add_note(note.get("note"), note.get("date"))
        if application.owner is not None:
            journal.set_owner(application.owner)
        journal.set_seal(application.has_seal())

        journal.add_related_application(application.id, dates.now())
        journal.set_in_doaj(True)

        if manual_update:
            journal.set_last_manual_update()

        if application.current_journal is not None:
            cj = models.Journal.pull(application.current_journal)

            # carry the id and the created date
            if cj is not None:
                journal.set_id(cj.id)
                journal.set_created(cj.created_date)

        if app.logger.isEnabledFor("debug"): app.logger.debug("Completing application_2_journal")

        return journal

    def journal_2_application(self, journal, account=None):
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

        if app.logger.isEnabledFor("debug"): app.logger.debug("Entering journal_2_application")

        # if an account is specified, check that it is allowed to perform this action
        if account is not None:
            try:
                self.can_create_update_request(account, journal)    # throws exception if not allowed
            except exceptions.AuthoriseException as e:
                msg = "Account {x} is not permitted to create an update request on journal {y}".format(x=account.id, y=journal.id)
                app.logger.info(msg)
                e.message = msg
                raise

        # copy all the relevant information from the journal to the application
        bj = journal.bibjson()
        contacts = journal.contacts()
        notes = journal.notes
        first_contact = None

        application = models.Suggestion()
        application.set_application_status("update_request")
        for c in contacts:
            application.add_contact(c.get("name"), c.get("email"))
            if first_contact is None:
                first_contact = c
        application.set_current_journal(journal.id)
        if journal.editor is not None:
            application.set_editor(journal.editor)
        if journal.editor_group is not None:
            application.set_editor_group(journal.editor_group)
        for n in notes:
            application.add_note(n.get("note"), n.get("date"))
        application.set_owner(journal.owner)
        application.set_seal(journal.has_seal())
        application.set_bibjson(bj)
        if first_contact is not None:
            application.set_suggester(first_contact.get("name"), first_contact.get("email"))

        if app.logger.isEnabledFor("debug"): app.logger.debug("Completed journal_2_application; return application object")
        return application

    def application(self, application_id):
        """
        Function to retrieve an application by its id

        :param application_id: the id of the application
        :return: Suggestion object
        """
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("application", [
            {"arg": application_id, "allow_none" : False, "arg_name" : "application_id"}
        ], exceptions.ArgumentException)

        # pull the application from the database
        return models.Suggestion.pull(application_id)

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
                the_lock = lock.lock("journal", journal_id, lock_account.id, lock_timeout)
            else:
                raise exceptions.ArgumentException("If you specify lock_journal on journal retrieval, you must also provide lock_account")

        return journal, the_lock

    def can_create_update_request(self, account, journal):
        """
        Is the given account allowed to create an update request from the given journal

        :param account: the account doing the action
        :param journal: the journal the account wants to create an update request from
        :return:
        """
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("can_create_update_request", [
            {"arg": account, "instance": models.Account, "allow_none" : False, "arg_name" : "account"},
            {"arg": journal, "instance": models.Journal, "allow_none" : False, "arg_name" : "journal"},
        ], exceptions.ArgumentException)

        # if this is the super user, they have all rights
        if account.is_super:
            return True

        if not account.has_role("publisher"):
            raise exceptions.AuthoriseException(reason=exceptions.AuthoriseException.WRONG_ROLE)
        if account.id != journal.owner:
            raise exceptions.AuthoriseException(reason=exceptions.AuthoriseException.NOT_OWNER)

        return True

    def can_edit_update_request(self, account, application):
        """
        Is the given account allowed to edit the update request application

        :param account: the account doing the action
        :param application: the application the account wants to edit
        :return:
        """
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("can_edit_update_request", [
            {"arg": account, "instance": models.Account, "allow_none" : False, "arg_name" : "account"},
            {"arg": application, "instance": models.Suggestion, "allow_none" : False, "arg_name" : "application"},
        ], exceptions.ArgumentException)

        # if this is the super user, they have all rights
        if account.is_super:
            return True

        if not account.has_role("publisher"):
            raise exceptions.AuthoriseException(reason=exceptions.AuthoriseException.WRONG_ROLE)
        if account.id != application.owner:
            raise exceptions.AuthoriseException(reason=exceptions.AuthoriseException.NOT_OWNER)
        if application.application_status not in ["update_request", "submitted"]:
            raise exceptions.AuthoriseException(reason=exceptions.AuthoriseException.WRONG_STATUS)

        return True

    def formcontext(self, type, role, source=None, form_data=None):
        """
        Method to retrieve the formcontext for the given type, role and to pass in the given source object

        :param type: supported types: "application"
        :param role: supported roles: "publisher"
        :param source: model object
        :return: FormContext instance
        """
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("can_edit_update_request", [
            {"arg": type, "instance": basestring, "allow_none" : False, "arg_name" : "type"},
            {"arg": role, "instance": basestring, "allow_none" : False, "arg_name" : "role"},
            {"arg": source, "instance": object, "allow_none" : True, "arg_name" : "source"},
            {"arg": form_data, "instace" : MultiDict, "allow_none" : True, "arg_name" : "form_data"},
        ], exceptions.ArgumentException)

        if type not in self.FORMCONTEXT_FACTORIES:
            raise exceptions.NoSuchFormContext()
        return self.FORMCONTEXT_FACTORIES[type].get_form_context(role=role, source=source, form_data=form_data)