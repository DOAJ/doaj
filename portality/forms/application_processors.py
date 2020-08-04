from datetime import datetime

from portality.core import app
from portality import models, constants, app_email
from portality.lib.formulaic import FormProcessor
import portality.notifications.application_emails as emails
from portality.ui.messages import Messages

from wtforms import FormField, FieldList


class NewApplication(FormProcessor):
    """
    Public Application Form Context.  This is also a sort of demonstrator as to how to implement
    one, so it will do unnecessary things like override methods that don't actually need to be overridden.

    This should be used in a context where an unauthenticated user is making a request to put a journal into the
    DOAJ.  It does not have any edit capacity (i.e. the form can only be submitted once), and it does not provide
    any form fields other than the essential journal bibliographic, application bibliographc and contact information
    for the suggester.  On submission, it will set the status to "pending" and the item will be available for review
    by the editors
    """

    ############################################################
    # PublicApplicationForm versions of FormProcessor lifecycle functions
    ############################################################

    def draft(self, account, id=None, *args, **kwargs):
        # check for validity
        valid = self.validate()

        # the draft to be saved needs to be valid
        if not valid:
            return None
        # def _resetDefaults(form):
        #     for field in form:
        #         if field.errors:
        #             if isinstance(field, FormField):
        #                 _resetDefaults(field.form)
        #             elif isinstance(field, FieldList):
        #                 for sub in field:
        #                     if isinstance(sub, FormField):
        #                         _resetDefaults(sub)
        #                     else:
        #                         sub.data = sub.default
        #             else:
        #                 field.data = field.default
        #
        # # if not valid, then remove all fields which have validation errors
        # if not valid:
        #     _resetDefaults(self.form)

        self.form2target()
        draft_application = models.DraftApplication(**self.target.data)
        if id is not None:
            draft_application.set_id(id)
        draft_application.set_owner(account.id)
        draft_application.save()
        return draft_application

    def finalise(self, account, save_target=True, email_alert=True):
        super(NewApplication, self).finalise()

        # set some administrative data
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.target.date_applied = now
        self.target.set_application_status(constants.APPLICATION_STATUS_PENDING)
        self.target.set_owner(account.id)
        self.target.set_last_manual_update()

        # Finally save the target
        if save_target:
            self.target.save()

        if email_alert:
            try:
                emails.send_received_email(self.target)
            except app_email.EmailException as e:
                self.add_alert(Messages.FORMS__APPLICATION_PROCESSORS__NEW_APPLICATION__FINALISE__USER_EMAIL_ERROR)
                app.logger.exception(Messages.FORMS__APPLICATION_PROCESSORS__NEW_APPLICATION__FINALISE__LOG_EMAIL_ERROR)


class AdminApplication(FormProcessor):

    def patch_target(self):
        pass

    def finalise(self, account, save_target=True, email_alert=True):
        super(AdminApplication, self).finalise()

        # fixme: do we need a save_target param? when don't we save?
        if save_target:
            self.target.save()
