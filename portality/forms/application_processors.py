from datetime import datetime

from portality.core import app
from portality import models, constants, app_email
from portality.lib.formulaic import FormProcessor
import portality.notifications.application_emails as emails


class PublicApplication(FormProcessor):
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

        # if not valid, then remove all fields which have validation errors
        if not valid:
            for field in self.form:
                if field.errors:
                    field.data = field.default

        self.form2target()
        draft_application = models.DraftApplication(**self.target.data)
        if id is not None:
            draft_application.set_id(id)
        draft_application.set_owner(account.id)
        draft_application.save()
        return draft_application

    def pre_validate(self):
        # no pre-validation requirements
        pass

    def patch_target(self):
        if self.source is not None:
            #self._carry_fixed_aspects()
            #self._merge_notes_forward()
            self.target.set_owner(self.source.owner)
            self.target.set_editor_group(self.source.editor_group)
            self.target.set_editor(self.source.editor)
            #self._carry_continuations()

            # we carry this over for completeness, although it will be overwritten in the finalise() method
            self.target.set_application_status(self.source.application_status)

    def finalise(self, save_target=True, email_alert=True):
        super(PublicApplication, self).finalise()

        # set some administrative data
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.target.date_applied = now
        self.target.set_application_status(constants.APPLICATION_STATUS_PENDING)

        # Finally save the target
        self.target.set_last_manual_update()
        if save_target:
            self.target.save()

        if email_alert:
            try:
                emails.send_received_email(self.target)
            except app_email.EmailException as e:
                self.add_alert("We were unable to send you an email confirmation - possible problem with the email address provided")
                app.logger.exception('Error sending application received email.')