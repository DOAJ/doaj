from portality.core import app
from portality.lib.argvalidate import argvalidate

from portality import models
from portality.formcontext import formcontext

from portality.bll import exceptions

from werkzeug.datastructures import MultiDict

class DOAJ(object):

    FORMCONTEXT_FACTORIES = {
        "application" : formcontext.ApplicationFormFactory
    }

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

        # if an account is specified, check that it is allowed to perform this action
        if account is not None:
            if not self.can_create_update_request(account, journal):
                raise exceptions.AuthoriseException("User " + account.id + " cannot create update requests for journal " + journal.id)

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
        application.set_editor(journal.editor)
        application.set_editor_group(journal.editor_group)
        for n in notes:
            application.add_note(n.get("note"), n.get("date"))
        application.set_owner(journal.owner)
        application.set_seal(journal.has_seal())
        application.set_bibjson(bj)
        application.set_suggester(first_contact.get("name"), first_contact.get("email"))

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

    def journal(self, journal_id):
        """
        Function to retrieve a journal by its id

        :param journal_id: the id of the journal
        :return: Journal object
        """
        # first validate the incoming arguments to ensure that we've got the right thing
        argvalidate("journal", [
            {"arg": journal_id, "allow_none" : False, "arg_name" : "journal_id"}
        ], exceptions.ArgumentException)

        return models.Journal.pull(journal_id)

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

        # allowed if the role publisher is set, and they account id is the journal owner
        return account.has_role("publisher") and account.id == journal.owner

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

        # allowed if the role publisher is set, the account owns the application, and the application is in an editable status
        return account.has_role("publisher") and account.id == application.owner and application.application_status in ["update_request", "submitted"]

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