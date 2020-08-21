import uuid
from datetime import datetime

from portality.core import app
from portality import models, constants, app_email
from portality.lib.formulaic import FormProcessor
import portality.notifications.application_emails as emails
from portality.ui.messages import Messages

from portality.crosswalks.application_form import ApplicationFormXWalk
from flask import url_for, request
from flask_login import current_user

from wtforms import FormField, FieldList


class ApplicationProcessor(FormProcessor):

    def _carry_fixed_aspects(self):
        if self.source is None:
            raise Exception("Cannot carry data from a non-existent source")

        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        # copy over any important fields from the previous version of the object
        created_date = self.source.created_date if self.source.created_date else now
        self.target.set_created(created_date)
        if "id" in self.source.data:
            self.target.data['id'] = self.source.data['id']

        try:
            if self.source.date_applied is not None:
                self.target.date_applied = self.source.date_applied
        except AttributeError:
            # fixme: should there always be a date_applied? Only true for applications
            pass

        try:
            if self.source.current_application:
                self.target.set_current_application(self.source.current_application)
        except AttributeError:
            # this means that the source doesn't know about current_applications, which is fine
            pass

        try:
            if self.source.current_journal:
                self.target.set_current_journal(self.source.current_journal)
        except AttributeError:
            # this means that the source doesn't know about current_journals, which is fine
            pass

        try:
            if self.source.related_journal:
                self.target.set_related_journal(self.source.related_journal)
        except AttributeError:
            # this means that the source doesn't know about related_journals, which is fine
            pass

        try:
            if self.source.related_applications:
                related = self.source.related_applications
                for rel in related:
                    self.target.add_related_application(rel.get("application_id"), rel.get("date_accepted"))
        except AttributeError:
            # this means that the source doesn't know about related_applications, which is fine
            pass

        # if the source is a journal, we need to carry the in_doaj flag
        if isinstance(self.source, models.Journal):
            self.target.set_in_doaj(self.source.is_in_doaj())

    def _merge_notes_forward(self, allow_delete=False):
        if self.source is None:
            raise Exception("Cannot carry data from a non-existent source")
        if self.target is None:
            raise Exception("Cannot carry data on to a non-existent target - run the xwalk first")

        # first off, get the notes (by reference) in the target and the notes from the source
        tnotes = self.target.notes
        snotes = self.source.notes

        # if there are no notes, we might not have the notes by reference, so later will
        # need to set them by value
        apply_notes_by_value = len(tnotes) == 0

        # for each of the target notes we need to get the original dates from the source notes
        for n in tnotes:
            for sn in snotes:
                if n.get("id") == sn.get("id"):
                    n["date"] = sn.get("date")

        # record the positions of any blank notes
        i = 0
        removes = []
        for n in tnotes:
            if n.get("note").strip() == "":
                removes.append(i)
            i += 1

        # actually remove all the notes marked for deletion
        removes.sort(reverse=True)
        for r in removes:
            tnotes.pop(r)

        # finally, carry forward any notes that aren't already in the target
        if not allow_delete:
            for sn in snotes:
                found = False
                for tn in tnotes:
                    if sn.get("id") == tn.get("id"):
                        found = True
                if not found:
                    tnotes.append(sn)

        if apply_notes_by_value:
            self.target.set_notes(tnotes)


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

        # FIXME: if you can only save a valid draft, you cannot save a draft
        # the draft to be saved needs to be valid
        #if not valid:
        #    return None

        def _resetDefaults(form):
            for field in form:
                if field.errors:
                    if isinstance(field, FormField):
                        _resetDefaults(field.form)
                    elif isinstance(field, FieldList):
                        for sub in field:
                            if isinstance(sub, FormField):
                                _resetDefaults(sub)
                            else:
                                sub.data = sub.default
                    else:
                        field.data = field.default

        # if not valid, then remove all fields which have validation errors
        if not valid:
            _resetDefaults(self.form)

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


class AdminApplication(ApplicationProcessor):

    def patch_target(self):
        if self.source is None:
            raise Exception("Can't patch a target from a non-existent source")

        self._carry_fixed_aspects()
        # This patches the target with things that shouldn't change from the source

        self._merge_notes_forward(allow_delete=True)
        # Notes

        # NOTE: this means you can't unset an owner once it has been set.  But you can change it.
        if (self.target.owner is None or self.target.owner == "") and (self.source.owner is not None):
            self.target.set_owner(self.source.owner)

    def finalise(self, account, save_target=True, email_alert=True):

        if self.source is None:
            raise Exception("You cannot edit a not-existent application")
        if self.source.application_status == constants.APPLICATION_STATUS_ACCEPTED:
            raise Exception("You cannot edit applications which have been accepted into DOAJ.")

        # if we are allowed to finalise, kick this up to the superclass
        super(AdminApplication, self).finalise()

        # FIXME: may want to factor this out of the suggestionformxwalk
        # If we have changed the editors assigned to this application, let them know.
        is_editor_group_changed = ApplicationFormXWalk.is_new_editor_group(self.form, self.source)
        is_associate_editor_changed = ApplicationFormXWalk.is_new_editor(self.form, self.source)

        # record the event in the provenance tracker
        models.Provenance.make(account, "edit", self.target)

        # delayed import of the DOAJ BLL
        from portality.bll.doaj import DOAJ
        applicationService = DOAJ.applicationService()

        # if this application is being accepted, then do the conversion to a journal
        if self.target.application_status == constants.APPLICATION_STATUS_ACCEPTED:
            j = applicationService.accept_application(self.target, current_user._get_current_object())
            # record the url the journal is available at in the admin are and alert the user
            jurl = url_for("doaj.toc", identifier=j.toc_id)
            if self.source.current_journal is not None:  # todo: are alerts displayed?
                self.add_alert('<a href="{url}" target="_blank">Existing journal updated</a>.'.format(url=jurl))
            else:
                self.add_alert('<a href="{url}" target="_blank">New journal created</a>.'.format(url=jurl))

            # Add the journal to the account and send the notification email
            try:
                owner = models.Account.pull(j.owner)
                self.add_alert('Associating the journal with account {username}.'.format(username=owner.id))
                owner.add_journal(j.id)
                if not owner.has_role('publisher'):
                    owner.add_role('publisher')
                owner.save()

                # for all acceptances, send an email to the owner of the journal
                self._send_application_approved_email(j.bibjson().title, owner.name, owner.email, self.source.current_journal is not None)
            except AttributeError:
                raise Exception("Account {owner} does not exist".format(owner=j.owner))
            except app_email.EmailException:
                self.add_alert("Problem sending email to suggester - probably address is invalid")
                app.logger.exception("Acceptance email to owner failed.")

        # if the application was instead rejected, carry out the rejection actions
        elif self.source.application_status != constants.APPLICATION_STATUS_REJECTED and self.target.application_status == constants.APPLICATION_STATUS_REJECTED:
            # remember whether this was an update request or not
            is_update_request = self.target.current_journal is not None

            # reject the application
            applicationService.reject_application(self.target, current_user._get_current_object())

            # if this was an update request, send an email to the owner
            if is_update_request:
                sent = False
                send_report = []
                try:
                    send_report = emails.send_publisher_reject_email(self.target, update_request=is_update_request)
                    sent = True
                except app_email.EmailException as e:
                    pass

                if sent:
                    self.add_alert(Messages.SENT_REJECTED_UPDATE_REQUEST_EMAIL.format(user=self.target.owner, email=send_report[0].get("email"), name=send_report[0].get("name")))
                else:
                    self.add_alert(Messages.NOT_SENT_REJECTED_UPDATE_REQUEST_EMAIL.format(user=self.target.owner))

        # the application was neither accepted or rejected, so just save it
        else:
            self.target.set_last_manual_update()
            self.target.save()

        # if revisions were requested, email the publisher
        if self.source.application_status != constants.APPLICATION_STATUS_REVISIONS_REQUIRED and self.target.application_status == constants.APPLICATION_STATUS_REVISIONS_REQUIRED:
            try:
                emails.send_publisher_update_request_revisions_required(self.target)
                self.add_alert(Messages.SENT_REJECTED_UPDATE_REQUEST_REVISIONS_REQUIRED_EMAIL.format(user=self.target.owner))
            except app_email.EmailException as e:
                self.add_alert(Messages.NOT_SENT_REJECTED_UPDATE_REQUEST_REVISIONS_REQUIRED_EMAIL.format(user=self.target.owner))

        # if we need to email the editor and/or the associate, handle those here
        if is_editor_group_changed:
            try:
                emails.send_editor_group_email(self.target)
            except app_email.EmailException:
                self.add_alert("Problem sending email to editor - probably address is invalid")
                app.logger.exception("Email to associate failed.")
        if is_associate_editor_changed:
            try:
                emails.send_assoc_editor_email(self.target)
            except app_email.EmailException:
                self.add_alert("Problem sending email to associate editor - probably address is invalid")
                app.logger.exception("Email to associate failed.")

        # If this is the first time this application has been assigned to an editor, notify the publisher.
        old_ed = self.source.editor
        if (old_ed is None or old_ed == '') and self.target.editor is not None:
            is_update_request = self.target.current_journal is not None
            if is_update_request:
                alerts = emails.send_publisher_update_request_editor_assigned_email(self.target)
            else:
                alerts = emails.send_publisher_application_editor_assigned_email(self.target)
            for alert in alerts:
                self.add_alert(alert)

        # Inform editor and associate editor if this application was 'ready' or 'completed', but has been changed to 'in progress'
        if (self.source.application_status == constants.APPLICATION_STATUS_READY or self.source.application_status == constants.APPLICATION_STATUS_COMPLETED) and self.target.application_status == constants.APPLICATION_STATUS_IN_PROGRESS:
            # First, the editor
            try:
                emails.send_editor_inprogress_email(self.target)
                self.add_alert('An email has been sent to notify the editor of the change in status.')
            except AttributeError:
                magic = str(uuid.uuid1())
                self.add_alert('Couldn\'t find a recipient for this email - check editor groups are correct. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
                app.logger.exception('No editor recipient for failed review email - ' + magic)
            except app_email.EmailException:
                magic = str(uuid.uuid1())
                self.add_alert('Sending the failed review email to editor didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
                app.logger.exception('Error sending review failed email to editor - ' + magic)

            # Then the associate
            try:
                emails.send_assoc_editor_inprogress_email(self.target)
                self.add_alert('An email has been sent to notify the assigned associate editor of the change in status.')
            except AttributeError:
                magic = str(uuid.uuid1())
                self.add_alert('Couldn\'t find a recipient for this email - check an associate editor is assigned. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
                app.logger.exception('No associate editor recipient for failed review email - ' + magic)
            except app_email.EmailException:
                magic = str(uuid.uuid1())
                self.add_alert('Sending the failed review email to associate editor didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
                app.logger.exception('Error sending review failed email to associate editor - ' + magic)

        # email other managing editors if this was newly set to 'ready'
        if self.source.application_status != constants.APPLICATION_STATUS_READY and self.target.application_status == constants.APPLICATION_STATUS_READY:
            # this template requires who made the change, say it was an Admin
            ed_id = 'an administrator'
            try:
                emails.send_admin_ready_email(self.target, editor_id=ed_id)
                self.add_alert('A confirmation email has been sent to the Managing Editors.')
            except app_email.EmailException:
                magic = str(uuid.uuid1())
                self.add_alert('Hm, sending the ready status to managing editors didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
                app.logger.exception('Error sending ready status email to managing editors - ' + magic)

    def _send_application_approved_email(self, journal_title, publisher_name, email, update_request=False):
        """Email the publisher when an application is accepted (it's here because it's too troublesome to factor out)"""
        url_root = request.url_root
        if url_root.endswith("/"):
            url_root = url_root[:-1]

        to = [email]
        fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
        subject = app.config.get("SERVICE_NAME", "") + " - journal accepted"
        publisher_name = publisher_name if publisher_name is not None else "Journal Owner"

        try:
            if app.config.get("ENABLE_PUBLISHER_EMAIL", False):
                msg = Messages.SENT_ACCEPTED_APPLICATION_EMAIL.format(email=email)
                template = "email/publisher_application_accepted.txt"
                if update_request:
                    msg = Messages.SENT_ACCEPTED_UPDATE_REQUEST_EMAIL.format(email=email)
                    template = "email/publisher_update_request_accepted.txt"
                jn = journal_title

                app_email.send_mail(to=to,
                                    fro=fro,
                                    subject=subject,
                                    template_name=template,
                                    journal_title=jn,
                                    publisher_name=publisher_name,
                                    url_root=url_root
                )
                self.add_alert(msg)
            else:
                msg = Messages.NOT_SENT_ACCEPTED_APPLICATION_EMAIL.format(email=email)
                if update_request:
                    msg = Messages.NOT_SENT_ACCEPTED_UPDATE_REQUEST_EMAIL.format(email=email)
                self.add_alert(msg)
        except Exception as e:
            magic = str(uuid.uuid1())
            self.add_alert('Hm, sending the journal acceptance information email didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
            app.logger.exception('Error sending application approved email failed - ' + magic)
