import uuid
from datetime import datetime

import portality.notifications.application_emails as emails
from portality.core import app
from portality import models, constants, app_email
from portality.lib.formulaic import FormProcessor
from portality.ui.messages import Messages
from portality.crosswalks.application_form import ApplicationFormXWalk
from portality.crosswalks.journal_form import JournalFormXWalk
from portality.bll import exceptions

from flask import url_for, request, has_request_context
from flask_login import current_user

from wtforms import FormField, FieldList


class ApplicationProcessor(FormProcessor):

    def pre_validate(self):
        # to bypass WTForms insistence that choices on a select field match the value, outside of the actual validation
        # chain
        super(ApplicationProcessor, self).pre_validate()

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

        try:
            if self.source.application_type:
                self.target.application_type = self.source.application_type
        except AttributeError:
            # this means that the source doesn't know about related_journals, which is fine
            pass

        # if the source is a journal, we need to carry the in_doaj flag
        if isinstance(self.source, models.Journal):
            self.target.set_in_doaj(self.source.is_in_doaj())

    def resetDefaults(self, form):
        # self.form.resettedFields = []
        def _values_to_reset(f):
            return (f.data != "") and (f.data != None) and (f.data != f.default)
        for field in form:
            if field.errors:
                if isinstance(field, FormField):
                    self.resetDefaults(field.form)
                elif isinstance(field, FieldList):
                    for sub in field:
                        if isinstance(sub, FormField):
                            self.resetDefaults(sub)
                        elif _values_to_reset(sub):
                            sub.data = sub.default
                elif _values_to_reset(field):
                    # self.form.resettedFields.append({"name": field.name, "data": field.data, "default": field.default})
                    field.data = field.default

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

    def _carry_continuations(self):
        if self.source is None:
            raise Exception("Cannot carry data from a non-existent source")

        try:
            sbj = self.source.bibjson()
            tbj = self.target.bibjson()
            if sbj.replaces:
                tbj.replaces = sbj.replaces
            if sbj.is_replaced_by:
                tbj.is_replaced_by = sbj.is_replaced_by
            if sbj.discontinued_date:
                tbj.discontinued_date = sbj.discontinued_date
        except AttributeError:
            # this means that the source doesn't know about current_applications, which is fine
            pass

    def _validate_status_change(self, source_status, target_status):
        """ Check whether the editorial pipeline permits a change to the target status for a role.
        Don't run this for admins, since they can change to any role at any time. """
        from portality.forms.application_forms import application_statuses
        choices_for_role = [s.get("value") for s in application_statuses(None, self._formulaic)]
        # choices_for_role = list(sum(application_statuses(None, self._formulaic), ()))
        # choices_for_role = list(sum(cls.application_status(role), ()))                     # flattens the list of tuples

        # Don't allow edits to application when status is beyond this user's permissions in the pipeline
        if source_status not in choices_for_role:
            raise Exception(
                "You don't have permission to edit applications which are in status {0}.".format(source_status))

        # Don't permit changes to status in reverse of the editorial process
        if choices_for_role.index(target_status) < choices_for_role.index(source_status):
            # Except that editors can revert 'completed' to 'in progress'
            if self._formulaic.name == 'editor' and source_status == constants.APPLICATION_STATUS_COMPLETED and target_status == constants.APPLICATION_STATUS_IN_PROGRESS:
                pass
            else:
                raise Exception(
                    "You are not permitted to revert the application status from {0} to {1}.".format(source_status,
                                                                                                     target_status))


class NewApplication(ApplicationProcessor):
    """
    Public Application Form Context.  This is also a sort of demonstrator as to how to implement
    one, so it will do unnecessary things like override methods that don't actually need to be overridden.

    This should be used in a context where an unauthenticated user is making a request to put a journal into the
    DOAJ.  It does not have any edit capacity (i.e. the form can only be submitted once), and it does not provide
    any form fields other than the essential journal bibliographic, application bibliographc and contact information
    for the suggester.  On submission, it will set the status to "pending" and the item will be available for review
    by the editors

    ~~NewApplication:FormProcessor~~
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

        # if not valid, then remove all fields which have validation errors
        if not valid:
            self.resetDefaults(self.form)

        self.form2target()
        # ~~-> DraftApplication:Model~~
        draft_application = models.DraftApplication(**self.target.data)
        if id is not None:
            draft_application.set_id(id)

        draft_application.set_application_status("draft")
        draft_application.set_owner(account.id)
        draft_application.save()
        return draft_application

    def finalise(self, account, save_target=True, email_alert=True, id=None):
        super(NewApplication, self).finalise()

        # set some administrative data
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.target.date_applied = now
        self.target.set_application_status(constants.APPLICATION_STATUS_PENDING)
        self.target.set_owner(account.id)
        self.target.set_last_manual_update()

        if id:
            # ~~-> Application:Model~~
            replacing = models.Application.pull(id)
            if replacing is None:
                self.target.set_id(id)
            else:
                if replacing.application_status == constants.APPLICATION_STATUS_PENDING and replacing.owner == account.id:
                    self.target.set_id(id)
                    self.target.set_created(replacing.created_date)

        # Finally save the target
        if save_target:
            self.target.save()
            # a draft may have been saved, so also remove that
            if id:
                models.DraftApplication.remove_by_id(id)

        if email_alert:
            try:
                emails.send_received_email(self.target)
            except app_email.EmailException as e:
                self.add_alert(Messages.FORMS__APPLICATION_PROCESSORS__NEW_APPLICATION__FINALISE__USER_EMAIL_ERROR)
                app.logger.exception(Messages.FORMS__APPLICATION_PROCESSORS__NEW_APPLICATION__FINALISE__LOG_EMAIL_ERROR)


class AdminApplication(ApplicationProcessor):
    """
    Managing Editor's Application Review form.  Should be used in a context where the form warrants full
    admin priviledges.  It will permit conversion of applications to journals, and assignment of owner account
    as well as assignment to editorial group.

    ~~ManEdApplication:FormProcessor~~
    """

    def pre_validate(self):
        # to bypass WTForms insistence that choices on a select field match the value, outside of the actual validation
        # chain
        super(AdminApplication, self).pre_validate()
        self.form.editor.choices = [(self.form.editor.data, self.form.editor.data)]

        # TODO: Should quick_reject be set through this form at all?
        self.form.quick_reject.choices = [(self.form.quick_reject.data, self.form.quick_reject.data)]

    def patch_target(self):
        super(AdminApplication, self).patch_target()

        # This patches the target with things that shouldn't change from the source
        self._carry_fixed_aspects()
        self._merge_notes_forward(allow_delete=True)

        # NOTE: this means you can't unset an owner once it has been set.  But you can change it.
        if (self.target.owner is None or self.target.owner == "") and (self.source.owner is not None):
            self.target.set_owner(self.source.owner)

    def finalise(self, account, save_target=True, email_alert=True):
        """
        account is the administrator account carrying out the action
        """

        if self.source is None:
            raise Exception("You cannot edit a not-existent application")
        if self.source.application_status == constants.APPLICATION_STATUS_ACCEPTED:
            raise Exception("You cannot edit applications which have been accepted into DOAJ.")

        # if we are allowed to finalise, kick this up to the superclass
        super(AdminApplication, self).finalise()

        # TODO: should these be a BLL feature?
        # If we have changed the editors assigned to this application, let them know.
        # ~~-> ApplicationForm:Crosswalk~~
        is_editor_group_changed = ApplicationFormXWalk.is_new_editor_group(self.form, self.source)
        is_associate_editor_changed = ApplicationFormXWalk.is_new_editor(self.form, self.source)

        # record the event in the provenance tracker
        # ~~-> Provenance:Model~~
        models.Provenance.make(account, "edit", self.target)

        # delayed import of the DOAJ BLL
        # ~~->Application:Service~~
        from portality.bll.doaj import DOAJ
        applicationService = DOAJ.applicationService()

        # if the application is already rejected, and we are moving it back into a non-rejected status
        if self.source.application_status == constants.APPLICATION_STATUS_REJECTED and self.target.application_status != constants.APPLICATION_STATUS_REJECTED:
            try:
                applicationService.unreject_application(self.target, current_user._get_current_object(), disallow_status=[])
            except exceptions.DuplicateUpdateRequest as e:
                self.add_alert(Messages.FORMS__APPLICATION_PROCESSORS__ADMIN_APPLICATION__FINALISE__COULD_NOT_UNREJECT)
                return

        # if this application is being accepted, then do the conversion to a journal
        if self.target.application_status == constants.APPLICATION_STATUS_ACCEPTED:
            j = applicationService.accept_application(self.target, account)
            # record the url the journal is available at in the admin are and alert the user
            if has_request_context():       # fixme: if we handle alerts via a notification service we won't have to toggle on request context
                jurl = url_for("doaj.toc", identifier=j.toc_id)
                if self.source.current_journal is not None:  # todo: are alerts displayed?
                    self.add_alert('<a href="{url}" target="_blank">Existing journal updated</a>.'.format(url=jurl))
                else:
                    self.add_alert('<a href="{url}" target="_blank">New journal created</a>.'.format(url=jurl))

            # Add the journal to the account and send the notification email
            try:
                # ~~-> Account:Model~~
                owner = models.Account.pull(j.owner)
                self.add_alert('Associating the journal with account {username}.'.format(username=owner.id))
                owner.add_journal(j.id)
                if not owner.has_role('publisher'):
                    owner.add_role('publisher')
                owner.save()

                # for all acceptances, send an email to the owner of the journal
                if email_alert:
                    self._send_application_approved_email(self.target, j, owner, self.source.current_journal is not None)
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
            if is_update_request and email_alert:
                # ~~-> Email:Notifications~~
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

        if email_alert:
            # ~~-> Email:Notifications~~
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
                    self.add_alert('Sending the ready status to managing editors didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
                    app.logger.exception('Error sending ready status email to managing editors - ' + magic)

    def _send_application_approved_email(self, application, journal, owner, update_request=False):
        """Email the publisher when an application is accepted (it's here because it's too troublesome to factor out)"""
        # ~~-> Email:Library~~
        url_root = request.url_root
        if url_root.endswith("/"):
            url_root = url_root[:-1]

        to = [owner.email]
        fro = app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org')
        if update_request:
            subject = app.config.get("SERVICE_NAME", "") + " - update request accepted"
        else:
            subject = app.config.get("SERVICE_NAME", "") + " - journal accepted"

        try:
            if app.config.get("ENABLE_PUBLISHER_EMAIL", False):
                msg = Messages.SENT_ACCEPTED_APPLICATION_EMAIL.format(email=owner.email)
                template = "email/publisher_application_accepted.jinja2"
                if update_request:
                    msg = Messages.SENT_ACCEPTED_UPDATE_REQUEST_EMAIL.format(email=owner.email)
                    template = "email/publisher_update_request_accepted.jinja2"

                app_email.send_mail(to=to,
                                    fro=fro,
                                    subject=subject,
                                    template_name=template,
                                    owner=owner,
                                    journal=journal,
                                    application=application)
                self.add_alert(msg)
            else:
                msg = Messages.NOT_SENT_ACCEPTED_APPLICATION_EMAIL.format(email=owner.email)
                if update_request:
                    msg = Messages.NOT_SENT_ACCEPTED_UPDATE_REQUEST_EMAIL.format(email=owner.email)
                self.add_alert(msg)
        except Exception as e:
            magic = str(uuid.uuid1())
            self.add_alert('Sending the journal acceptance information email didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
            app.logger.exception('Error sending application approved email failed - ' + magic)

    def validate(self):
        _statuses_not_requiring_validation = ['rejected', 'pending', 'in progress', 'on hold']
        self.pre_validate()
        # make use of the ability to disable validation, otherwise, let it run
        valid = super(AdminApplication, self).validate()

        if self.form is not None:
            if self.form.application_status.data in _statuses_not_requiring_validation and not valid:
                self.resetDefaults(self.form)
                return True

        return valid


class EditorApplication(ApplicationProcessor):
    """
    Editors Application Review form.  This should be used in a context where an editor who owns an editorial group
    is accessing an application.  This prevents re-assignment of Editorial group, but permits assignment of associate
    editor.  It also permits change in application state, except to "accepted"; therefore this form context cannot
    be used to create journals from applications. Deleting notes is not allowed, but adding is.

    ~~EditorApplication:FormProcessor~~
    """

    def validate(self):
        _statuses_not_requiring_validation = ['pending', 'in progress']
        self.pre_validate()
        # make use of the ability to disable validation, otherwise, let it run
        valid = super(EditorApplication, self).validate()

        if self.form is not None:
            if self.form.application_status.data in _statuses_not_requiring_validation and not valid:
                self.resetDefaults(self.form)
                return True

        return valid

    def pre_validate(self):
        # Call to super sets all the basic disabled fields
        super(EditorApplication, self).pre_validate()

        # although the editor_group field is handled by the general pre-validator, we still need to set the choices
        # self.form.editor_group.data = self.source.editor_group
        self.form.editor.choices = [(self.form.editor.data, self.form.editor.data)]

        # This is no longer necessary, is handled by the main pre_validate function
        #if self._formulaic.get('application_status').is_disabled:
        #    self.form.application_status.data = self.source.application_status
        # but we do still need to add the overwritten status to the choices for validation
        if self.form.application_status.data not in [c[0] for c in self.form.application_status.choices]:
            self.form.application_status.choices.append((self.form.application_status.data, self.form.application_status.data))

    def patch_target(self):
        super(EditorApplication, self).patch_target()

        self._carry_fixed_aspects()
        self._merge_notes_forward()
        self._carry_continuations()

        self.target.set_owner(self.source.owner)
        self.target.set_editor_group(self.source.editor_group)

    def finalise(self):
        if self.source is None:
            raise Exception("You cannot edit a not-existent application")
        if self.source.application_status == constants.APPLICATION_STATUS_ACCEPTED:
            raise Exception("You cannot edit applications which have been accepted into DOAJ.")

        # if we are allowed to finalise, kick this up to the superclass
        super(EditorApplication, self).finalise()

        # Check the status change is valid
        self._validate_status_change(self.source.application_status, self.target.application_status)

        # ~~-> ApplicationForm:Crosswalk~~
        new_associate_assigned = ApplicationFormXWalk.is_new_editor(self.form, self.source)

        # Save the target
        self.target.set_last_manual_update()
        self.target.save()

        # record the event in the provenance tracker
        # ~~-> Procenance:Model~~
        models.Provenance.make(current_user, "edit", self.target)

        # if we need to email the associate because they have just been assigned, handle that here.
        # ~~-> Email:Notifications~~
        if new_associate_assigned:
            try:
                self.add_alert("New editor assigned - email with confirmation has been sent")
                emails.send_assoc_editor_email(self.target)
            except app_email.EmailException:
                self.add_alert("Problem sending email to associate editor - probably address is invalid")
                app.logger.exception('Error sending associate assigned email')

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

        # Email the assigned associate if the application was reverted from 'completed' to 'in progress' (failed review)
        if self.source.application_status == constants.APPLICATION_STATUS_COMPLETED and self.target.application_status == constants.APPLICATION_STATUS_IN_PROGRESS:
            try:
                emails.send_assoc_editor_inprogress_email(self.target)
                self.add_alert(
                    'An email has been sent to notify the assigned associate editor of the change in status.')
            except AttributeError as e:
                magic = str(uuid.uuid1())
                self.add_alert(
                    'Couldn\'t find a recipient for this email - check an associate editor is assigned. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
                app.logger.exception('No associate editor recipient for failed review email - ' + magic)
            except app_email.EmailException:
                magic = str(uuid.uuid1())
                self.add_alert(
                    'Sending the failed review email to associate editor didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
                app.logger.exception('Error sending failed review email to associate editor - ' + magic)

        # email managing editors if the application was newly set to 'ready'
        if self.source.application_status != constants.APPLICATION_STATUS_READY and self.target.application_status == constants.APPLICATION_STATUS_READY:
            # Tell the ManEds who has made the status change - the editor in charge of the group
            # ~~-> EditorGroup:Model~~
            editor_group_name = self.target.editor_group
            editor_group_id = models.EditorGroup.group_exists_by_name(name=editor_group_name)
            editor_group = models.EditorGroup.pull(editor_group_id)
            editor_acc = editor_group.get_editor_account()

            # record the event in the provenance tracker
            # ~~-> Provenance:Model~~
            models.Provenance.make(current_user, "status:ready", self.target)

            editor_id = editor_acc.id
            try:
                # ~~-> Email:Notifications~~
                emails.send_admin_ready_email(self.target, editor_id=editor_id)
                self.add_alert('A confirmation email has been sent to the Managing Editors.')
            except app_email.EmailException:
                magic = str(uuid.uuid1())
                self.add_alert(
                    'Sending the ready status to managing editors didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
                app.logger.exception('Error sending ready status email to managing editors - ' + magic)


class AssociateApplication(ApplicationProcessor):
    """
       Associate Editors Application Review form. This is to be used in a context where an associate editor (fewest rights)
       needs to access an application for review. This editor cannot change the editorial group or the assigned editor.
       They also cannot change the owner of the application. They cannot set an application to "Accepted" so this form can't
       be used to create a journal from an application. They cannot delete, only add notes.

       ~~AssEdApplication:FormProcessor~~
       """

    def pre_validate(self):
        # Call to super sets all the basic disabled fields
        super(AssociateApplication, self).pre_validate()

        # no longer necessary, handled by superclass pre_validate
        #if self._formulaic.get('application_status').is_disabled:
        #    self.form.application_status.data = self.source.application_status
        # but we do still need to add the overwritten status to the choices for validation
        if self.form.application_status.data not in [c[0] for c in self.form.application_status.choices]:
            self.form.application_status.choices.append(
                (self.form.application_status.data, self.form.application_status.data))

    def patch_target(self):
        if self.source is None:
            raise Exception("You cannot patch a target from a non-existent source")

        self._carry_fixed_aspects()
        self._merge_notes_forward()
        self.target.set_owner(self.source.owner)
        self.target.set_editor_group(self.source.editor_group)
        self.target.set_editor(self.source.editor)
        self.target.set_seal(self.source.has_seal())
        self._carry_continuations()

    def finalise(self):
        # if we are allowed to finalise, kick this up to the superclass
        super(AssociateApplication, self).finalise()

        # Check the status change is valid
        self._validate_status_change(self.source.application_status, self.target.application_status)
        # Choices.validate_status_change('associate', self.source.application_status, self.target.application_status)

        # Save the target
        self.target.set_last_manual_update()
        self.target.save()

        # record the event in the provenance tracker
        # ~~-> Provenance:Model~~
        models.Provenance.make(current_user, "edit", self.target)

        # inform publisher if this was set to 'in progress' from 'pending'
        if self.source.application_status == constants.APPLICATION_STATUS_PENDING and self.target.application_status == constants.APPLICATION_STATUS_IN_PROGRESS:
            if app.config.get("ENABLE_PUBLISHER_EMAIL", False):
                # ~~-> Email:Notifications~~
                is_update_request = self.target.current_journal is not None
                if is_update_request:
                    alerts = emails.send_publisher_update_request_inprogress_email(self.target)
                else:
                    alerts = emails.send_publisher_application_inprogress_email(self.target)
                for alert in alerts:
                    self.add_alert(alert)
            else:
                self.add_alert(Messages.IN_PROGRESS_NOT_SENT_EMAIL_DISABLED)

        # inform editor if this was newly set to 'completed'
        if self.source.application_status != constants.APPLICATION_STATUS_COMPLETED and self.target.application_status == constants.APPLICATION_STATUS_COMPLETED:
            # record the event in the provenance tracker
            # ~~-> Procenance:Model~~
            models.Provenance.make(current_user, "status:completed", self.target)

            try:
                # ~~-> Email:Notifications~~
                emails.send_editor_completed_email(self.target)
                self.add_alert('A confirmation email has been sent to notify the editor of the change in status.')
            except app_email.EmailException:
                magic = str(uuid.uuid1())
                self.add_alert(
                    'Sending the ready status to editor email didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
                app.logger.exception('Error sending completed status email to editor - ' + magic)


class PublisherUpdateRequest(ApplicationProcessor):
    """
    ~~PublisherUpdateRequest:FormProcessor~~
    """

    def pre_validate(self):
        if self.source is None:
            raise Exception("You cannot validate a form from a non-existent source")

        super(ApplicationProcessor, self).pre_validate()

    def patch_target(self):
        if self.source is None:
            raise Exception("You cannot patch a target from a non-existent source")

        self._carry_subjects_and_seal()
        self._carry_fixed_aspects()
        self._merge_notes_forward()
        self.target.set_owner(self.source.owner)
        self.target.set_editor_group(self.source.editor_group)
        self.target.set_editor(self.source.editor)
        self._carry_continuations()

        # we carry this over for completeness, although it will be overwritten in the finalise() method
        self.target.set_application_status(self.source.application_status)

    def finalise(self, save_target=True, email_alert=True):
        # FIXME: this first one, we ought to deal with outside the form context, but for the time being this
        # can be carried over from the old implementation
        if self.source is None:
            raise Exception("You cannot edit a not-existent application")

        # if we are allowed to finalise, kick this up to the superclass
        super(PublisherUpdateRequest, self).finalise()

        # set the status to update_request (if not already)
        self.target.set_application_status(constants.APPLICATION_STATUS_UPDATE_REQUEST)

        # Save the target
        self.target.set_last_manual_update()
        if save_target:
            saved = self.target.save()
            if saved is None:
                raise Exception("Save on application failed")

        # obtain the related journal, and attach the current application id to it
        # ~~-> Journal:Service~~
        journal_id = self.target.current_journal
        from portality.bll.doaj import DOAJ
        journalService = DOAJ.journalService()
        if journal_id is not None:
            journal, _ = journalService.journal(journal_id)
            if journal is not None:
                journal.set_current_application(self.target.id)
                if save_target:
                    saved = journal.save()
                    if saved is None:
                        raise Exception("Save on journal failed")
            else:
                self.target.remove_current_journal()

        # email the publisher to tell them we received their update request
        if email_alert:
            try:
                # ~~-> Email:Notifications~~
                self._send_received_email()
            except app_email.EmailException as e:
                self.add_alert("We were unable to send you an email confirmation - possible problem with your email address")
                app.logger.exception('Error sending reapplication received email to publisher')

    def _carry_subjects_and_seal(self):
        # carry over the subjects
        source_subjects = self.source.bibjson().subject
        self.target.bibjson().subject = source_subjects

        # carry over the seal
        self.target.set_seal(self.source.has_seal())

    def _send_received_email(self):
        # ~~-> Account:Model~~
        acc = models.Account.pull(self.target.owner)
        if acc is None:
            self.add_alert("Unable to locate account for specified owner")
            return

        # ~~-> Email:Library~~
        to = [acc.email]
        fro = app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org')
        subject = app.config.get("SERVICE_NAME","") + " - update request received"

        try:
            if app.config.get("ENABLE_PUBLISHER_EMAIL", False):
                app_email.send_mail(to=to,
                                    fro=fro,
                                    subject=subject,
                                    template_name="email/publisher_update_request_received.jinja2",
                                    application=self.target,
                                    owner=acc)
                self.add_alert('A confirmation email has been sent to ' + acc.email + '.')
        except app_email.EmailException as e:
            magic = str(uuid.uuid1())
            self.add_alert('Hm, sending the "update request received" email didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
            app.logger.error(magic + "\n" + repr(e))
            raise e


class PublisherUpdateRequestReadOnly(ApplicationProcessor):
    """
    Read Only Application form for publishers. Nothing can be changed. Useful to show publishers what they
    currently have submitted for review

    ~~PublisherUpdateRequestReadOnly:FormProcessor~~
    """

    def finalise(self):
        raise Exception("You cannot edit applications using the read-only form")


###############################################
### Journal form processors
###############################################

class ManEdJournalReview(ApplicationProcessor):
    """
    Managing Editor's Journal Review form.  Should be used in a context where the form warrants full
    admin privileges.  It will permit doing every action.

    ~~ManEdJournal:FormProcessor~~
    """
    def patch_target(self):
        if self.source is None:
            raise Exception("You cannot patch a target from a non-existent source")

        self._carry_fixed_aspects()
        self._merge_notes_forward(allow_delete=True)

        # NOTE: this means you can't unset an owner once it has been set.  But you can change it.
        if (self.target.owner is None or self.target.owner == "") and (self.source.owner is not None):
            self.target.set_owner(self.source.owner)

    def finalise(self):
        # FIXME: this first one, we ought to deal with outside the form context, but for the time being this
        # can be carried over from the old implementation

        if self.source is None:
            raise Exception("You cannot edit a not-existent journal")

        # if we are allowed to finalise, kick this up to the superclass
        super(ManEdJournalReview, self).finalise()

        # If we have changed the editors assinged to this application, let them know.
        # ~~-> JournalForm:Crosswalk~~
        is_editor_group_changed = JournalFormXWalk.is_new_editor_group(self.form, self.source)
        is_associate_editor_changed = JournalFormXWalk.is_new_editor(self.form, self.source)

        # Save the target
        self.target.set_last_manual_update()
        self.target.save()

        # if we need to email the editor and/or the associate, handle those here
        # ~~-> Email:Notifications~~
        if is_editor_group_changed:
            try:
                emails.send_editor_group_email(self.target)
            except app_email.EmailException:
                self.add_alert("Problem sending email to editor - probably address is invalid")
                app.logger.exception('Error sending assignment email to editor.')
        if is_associate_editor_changed:
            try:
                emails.send_assoc_editor_email(self.target)
            except app_email.EmailException:
                self.add_alert("Problem sending email to associate editor - probably address is invalid")
                app.logger.exception('Error sending assignment email to associate.')

    def validate(self):
        # make use of the ability to disable validation, otherwise, let it run
        if self.form is not None:
            if self.form.make_all_fields_optional.data:
                self.pre_validate()
                return True

        return super(ManEdJournalReview, self).validate()


class EditorJournalReview(ApplicationProcessor):
    """
    Editors Journal Review form.  This should be used in a context where an editor who owns an editorial group
    is accessing a journal.  This prevents re-assignment of Editorial group, but permits assignment of associate
    editor.

    ~~EditorJournal:FormProcessor~~
    """

    def patch_target(self):
        if self.source is None:
            raise Exception("You cannot patch a target from a non-existent source")

        self._carry_fixed_aspects()
        self.target.set_owner(self.source.owner)
        self.target.set_editor_group(self.source.editor_group)
        self._merge_notes_forward()
        self._carry_continuations()

    def pre_validate(self):
        # call to super handles all the basic disabled field
        super(EditorJournalReview, self).pre_validate()

        # although the superclass sets the value of the disabled field, we still need to set the choices
        # self.form.editor_group.data = self.source.editor_group
        self.form.editor.choices = [(self.form.editor.data, self.form.editor.data)]

    def finalise(self):
        if self.source is None:
            raise Exception("You cannot edit a not-existent journal")

        # if we are allowed to finalise, kick this up to the superclass
        super(EditorJournalReview, self).finalise()

        # ~~-> ApplicationForm:Crosswalk~~
        email_associate = ApplicationFormXWalk.is_new_editor(self.form, self.source)

        # Save the target
        self.target.set_last_manual_update()
        self.target.save()

        # if we need to email the associate, handle that here.
        if email_associate:
            # ~~-> Email:Notifications~~
            try:
                emails.send_assoc_editor_email(self.target)
            except app_email.EmailException:
                self.add_alert("Problem sending email to associate editor - probably address is invalid")
                app.logger.exception('Error sending assignment email to associate.')


class AssEdJournalReview(ApplicationProcessor):
    """
    Associate Editors Journal Review form. This is to be used in a context where an associate editor (fewest rights)
    needs to access a journal for review. This editor cannot change the editorial group or the assigned editor.
    They also cannot change the owner of the journal. They cannot delete, only add notes.

    ~~AssEdJournal:FormProcessor~~
    """

    def patch_target(self):
        if self.source is None:
            raise Exception("You cannot patch a target from a non-existent source")

        self._carry_fixed_aspects()
        self._merge_notes_forward()
        self.target.set_owner(self.source.owner)
        self.target.set_editor_group(self.source.editor_group)
        self.target.set_editor(self.source.editor)
        self._carry_continuations()

    def finalise(self):
        if self.source is None:
            raise Exception("You cannot edit a not-existent journal")

        # if we are allowed to finalise, kick this up to the superclass
        super(AssEdJournalReview, self).finalise()

        # Save the target
        self.target.set_last_manual_update()
        self.target.save()


class ReadOnlyJournal(ApplicationProcessor):
    """
    Read Only Journal form. Nothing can be changed. Useful for reviewing a journal and an application
    (or update request) side by side in 2 browser windows or tabs.

    ~~ReadOnlyJournal:FormProcessor~~
    """
    def form2target(self):
        pass  # you can't edit objects using this form

    def patch_target(self):
        pass  # you can't edit objects using this form

    def finalise(self):
        raise Exception("You cannot edit journals using the read-only form")


class ManEdBulkEdit(ApplicationProcessor):
    """
    Managing Editor's Journal Review form.  Should be used in a context where the form warrants full
    admin privileges.  It will permit doing every action.

    ~~ManEdBulkJournal:FormProcessor~~
    """
    pass
