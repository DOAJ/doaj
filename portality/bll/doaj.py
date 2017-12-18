from portality import models
from portality.formcontext import formcontext


from portality.bll import exceptions

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
        if account is not None:
            if not self.can_create_update_request(account, journal):
                raise exceptions.AuthoriseException("User " + account.id + " cannot create update requests for journal " + journal.id)

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
        return models.Suggestion.pull(application_id)

    def journal(self, journal_id):
        """
        Function to retrieve a journal by its id

        :param journal_id: the id of the journal
        :return: Journal object
        """
        return models.Journal.pull(journal_id)

    def can_create_update_request(self, account, journal):
        """
        Is the given account allowed to create an update request from the given journal

        :param account: the account doing the action
        :param journal: the journal the account wants to create an update request from
        :return:
        """
        if account.is_super:
            return True
        return account.has_role("publisher") and account.id == journal.owner

    def can_edit_update_request(self, account, application):
        """
        Is the given account allowed to edit the update request application

        :param account: the account doing the action
        :param application: the application the account wants to edit
        :return:
        """
        if account.is_super:
            return True
        return account.has_role("publisher") and account.id == application.owner and application.application_status in ["update_request", "submitted"]

    def formcontext(self, type, role, source=None, form_data=None):
        """
        Method to retrieve the formcontext for the given type, role and to pass in the given source object

        :param type: supported types: "application"
        :param role: supported roles: "publisher"
        :param source: model object
        :return: FormContext instance
        """
        if type not in self.FORMCONTEXT_FACTORIES:
            raise exceptions.NoSuchFormContext()
        return self.FORMCONTEXT_FACTORIES[type].get_form_context(role=role, source=source, form_data=form_data)