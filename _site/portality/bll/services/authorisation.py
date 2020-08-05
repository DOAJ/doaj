from portality.lib.argvalidate import argvalidate
from portality import models, constants
from portality.bll import exceptions


class AuthorisationService(object):
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

    def can_edit_application(self, account, application):
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
        if application.application_status not in [
                constants.APPLICATION_STATUS_PENDING,
                constants.APPLICATION_STATUS_UPDATE_REQUEST,
                constants.APPLICATION_STATUS_REVISIONS_REQUIRED
            ]:
            raise exceptions.AuthoriseException(reason=exceptions.AuthoriseException.WRONG_STATUS)

        return True

    def can_view_application(self, account, application):
        """
        Is the given account allowed to view the update request application

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

        return True
