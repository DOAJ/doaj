import json
import uuid
from datetime import datetime

from flask import render_template, url_for, request
from flask_login import current_user

from portality import constants
from portality import models, app_email, util
from portality.core import app
from portality.formcontext import forms, xwalk, render, choices, FormContextException
from portality.lcc import lcc_jstree
from portality.ui.messages import Messages
import portality.notifications.application_emails as emails

from portality.forms.application_forms import FORMS, PYTHON_FUNCTIONS, JAVASCRIPT_FUNCTIONS

ACC_MSG = 'Please note you <span class="red">cannot edit</span> this application as it has been accepted into the DOAJ.'
SCOPE_MSG = 'Please note you <span class="red">cannot edit</span> this application as you don\'t have the necessary ' \
            'account permissions to edit applications which are {0}.'

FIELDS_WITH_DESCRIPTION = ["publisher", "society_institution", "platform", "title", "alternative_title"]
URL_FIELDS = ["url", "processing_charges_url", "submission_charges_url", "articles_last_year_url", "digital_archiving_policy_url", "editorial_board_url", "review_process_url", "instructions_authors_url", "oa_statement_url", "license_url", "waiver_policy_url", "download_statistics_url", "copyright_url", "publishing_rights_url", "plagiarism_screening_url", "license_embedded_url", "aims_scope_url"]


class FormContext(object):
    def __init__(self, form_data=None, source=None, formulaic_context=None):
        # initialise our core properties
        self._source = source
        self._target = None
        self._form_data = form_data
        self._form = None
        self._renderer = None
        self._template = None
        self._alert = []
        self._info = ''
        self._formulaic = formulaic_context

        # initialise the renderer (falling back to a default if necessary)
        self.make_renderer()
        if self.renderer is None:
            self.renderer = render.Renderer()

        # specify the jinja template that will wrap the renderer
        self.set_template()

        # now create our form instance, with the form_data (if there is any)
        if form_data is not None:
            self.data2form()

        # if there isn't any form data, then we should create the form properties from source instead
        elif source is not None:
            self.source2form()

        # if there is no source, then a blank form object
        else:
            self.blank_form()

    ############################################################
    # getters and setters on the main FormContext properties
    ############################################################

    @property
    def form(self):
        return self._form

    @form.setter
    def form(self, val):
        self._form = val

    @property
    def source(self):
        return self._source

    @property
    def form_data(self):
        return self._form_data

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, val):
        self._target = val

    @property
    def renderer(self):
        return self._renderer

    @renderer.setter
    def renderer(self, val):
        self._renderer = val

    @property
    def template(self):
        return self._template

    @template.setter
    def template(self, val):
        self._template = val

    @property
    def alert(self):
        return self._alert

    def add_alert(self, val):
        self._alert.append(val)

    @property
    def info(self):
        return self._info

    @info.setter
    def info(self, val):
        self._info = val

    ############################################################
    # Lifecycle functions that subclasses should implement
    ############################################################

    def make_renderer(self):
        """
        This will be called during init, and must populate the self.render property
        """
        pass

    def set_template(self):
        """
        This will be called during init, and must populate the self.template property with the path to the jinja template
        """
        pass

    def pre_validate(self):
        """
        This will be run before validation against the form is run.
        Use it to patch the form with any relevant data, such as fields which were disabled
        """
        pass

    def blank_form(self):
        """
        This will be called during init, and must populate the self.form_data property with an instance of the form in this
        context, based on no originating source or form data
        """
        pass

    def data2form(self):
        """
        This will be called during init, and must convert the form_data into an instance of the form in this context,
        and write to self.form
        """
        pass

    def source2form(self):
        """
        This will be called during init, and must convert the source object into an instance of the form in this
        context, and write to self.form
        """
        pass

    def form2target(self):
        """
        Convert the form object into a the target system object, and write to self.target
        """
        pass

    def patch_target(self):
        """
        Patch the target with data from the source.  This will be run by the finalise method (unless you override it)
        """
        pass

    def finalise(self, *args, **kwargs):
        """
        Finish up with the FormContext.  Carry out any final workflow tasks, etc.
        """
        self.form2target()
        self.patch_target()

    ############################################################
    # Functions which can be called directly, but may be overridden if desired
    ############################################################

    def validate(self):
        self.pre_validate()
        f = self.form
        valid = False
        if f is not None:
            valid = f.validate()

        # if this isn't a valid form, record the fields that have errors
        # with the renderer for use later
        if not valid:
            error_fields = []
            for field in self.form:
                if field.errors:
                    error_fields.append(field.short_name)

        return valid

    @property
    def errors(self):
        f = self.form
        if f is not None:
            return f.errors
        return False

    def render_template(self, **kwargs):
        return render_template(self.template, form_context=self, **kwargs)

    #def render_field_group(self, field_group_name=None, **kwargs):
    #    return self.renderer.render_field_group(self, field_group_name, **kwargs)

    def fieldset(self, fieldset_name=None):
        return self._formulaic.fieldset(fieldset_name)

    def fieldsets(self):
        return self._formulaic.fieldsets()

    def check_field_group_exists(self, field_group_name):
        return self.renderer.check_field_group_exists(field_group_name)

    @property
    def ui_settings(self):
        return self._formulaic.ui_settings

class PrivateContext(FormContext):
    def _expand_descriptions(self, fields):
        # add the contents of a few fields to their descriptions since select2 autocomplete
        # would otherwise obscure the full values
        for field in fields:
            if field in self.form.data:
                if self.form[field].data:
                    if not self.form[field].description:
                        self.form[field].description = 'Full contents: ' + self.form[field].data
                    else:
                        self.form[field].description += '<br><br>Full contents: ' + self.form[field].data

    def _expand_url_descriptions(self, fields):
        # add the contents of a few fields to their descriptions since select2 autocomplete
        # would otherwise obscure the full values
        for field in fields:
            if field in self.form.data:
                if self.form[field].data:
                    if not self.form[field].description:
                        self.form[field].description = 'Full contents: <a href=' + self.form[field].data + " target='_blank'>" + self.form[field].data + "</a>"
                    else:
                        self.form[field].description += '<br><br>Full contents: <a href=' + self.form[field].data + " target='_blank'>" + self.form[field].data + "</a>"

    def _carry_fixed_aspects(self):
        if self.source is None:
            raise FormContextException("Cannot carry data from a non-existent source")

        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        # copy over any important fields from the previous version of the object
        created_date = self.source.created_date if self.source.created_date else now
        self.target.set_created(created_date)
        if "id" in self.source.data:
            self.target.data['id'] = self.source.data['id']

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

    @staticmethod
    def _subjects2str(subjects):
        subject_strings = []
        for sub in subjects:
            subject_strings.append('{term}'.format(term=sub.get('term')))
        return ', '.join(subject_strings)

    def _merge_notes_forward(self, allow_delete=False):
        if self.source is None:
            raise FormContextException("Cannot carry data from a non-existent source")
        if self.target is None:
            raise FormContextException("Cannot carry data on to a non-existent target - run the xwalk first")

        # first off, get the notes (by reference) in the target and the notes from the source
        tnotes = self.target.notes
        snotes = self.source.notes

        # if there are no notes, we might not have the notes by reference, so later will
        # need to set them by value
        apply_notes_by_value = len(tnotes) == 0

        # for each of the target notes we need to get the original dates from the source notes
        for n in tnotes:
            for sn in snotes:
                if n.get("note") == sn.get("note"):
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
                    if sn.get("note") == tn.get("note"):
                        found = True
                if not found:
                    tnotes.append(sn)

        if apply_notes_by_value:
            self.target.set_notes(tnotes)

    def _populate_editor_field(self, editor_group_name):
        """Set the editor field choices from a given editor group name"""
        if editor_group_name is None:
            self.form.editor.choices = [("", "")]
        else:
            eg = models.EditorGroup.pull_by_key("name", editor_group_name)
            if eg is not None:
                editors = [eg.editor]
                editors += eg.associates
                editors = list(set(editors))
                self.form.editor.choices = [("", "Choose an editor")] + [(editor, editor) for editor in editors]
            else:
                self.form.editor.choices = [("", "")]

    def _validate_editor_field(self):
        """ Validate the choice of editor, which could be out of sync with the group in exceptional circumstances """
        editor = self.form.editor.data
        if editor is not None and editor != "":
            editor_group_name = self.form.editor_group.data
            if editor_group_name is not None and editor_group_name != "":
                eg = models.EditorGroup.pull_by_key("name", editor_group_name)
                if eg is not None:
                    all_eds = eg.associates + [eg.editor]
                    if editor in all_eds:
                        return  # success - an editor group was found and our editor was in it
                raise FormContextException("Editor '{0}' not found in editor group '{1}'".format(editor, editor_group_name))
            else:
                raise FormContextException("An editor has been assigned without an editor group")

    def _carry_continuations(self):
        if self.source is None:
            raise FormContextException("Cannot carry data from a non-existent source")

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


class ApplicationContext(PrivateContext):
    ERROR_MSG_TEMPLATE = \
        """Problem while creating account while turning suggestion into journal.
        There should be a {missing_thing} on user {username} but there isn't.
        Created the user but not sending the email.
        """.replace("\n", ' ')

    def _carry_fixed_aspects(self):
        super(ApplicationContext, self)._carry_fixed_aspects()
        if self.source.suggested_on is not None:
            self.target.suggested_on = self.source.suggested_on

    def _create_account_on_suggestion_approval(self, suggestion, journal):
        o = models.Account.pull(suggestion.owner)
        if o:
            self.add_alert('Account {username} already exists, so simply associating the journal with it.'.format(username=o.id))
            o.add_journal(journal.id)
            if not o.has_role('publisher'):
                o.add_role('publisher')
            o.save()
            return o

        suggestion_contact = util.listpop(suggestion.contacts())
        if not suggestion_contact.get('email'):
            msg = self.ERROR_MSG_TEMPLATE.format(username=o.id, missing_thing='journal contact email in the application')
            app.logger.error(msg)
            self.add_alert(msg)
            return o

        send_info_to = suggestion_contact.get('email')
        o = models.Account.make_account(
            suggestion.owner,
            name=suggestion_contact.get('name'),
            email=send_info_to,
            roles=['publisher'],
            associated_journal_ids=[journal.id]
        )

        o.save()

        if not o.reset_token:
            msg = self.ERROR_MSG_TEMPLATE.format(username=o.id, missing_thing='reset token')
            app.logger.error(msg)
            self.add_alert(msg)
            return o

        url_root = request.url_root
        if url_root.endswith("/"):
            url_root = url_root[:-1]
        reset_url = url_root + url_for('account.reset', reset_token=o.reset_token)
        forgot_pw_url = url_root + url_for('account.forgot')

        password_create_timeout_seconds = int(app.config.get("PASSWORD_CREATE_TIMEOUT", app.config.get('PASSWORD_RESET_TIMEOUT', 86400) * 14))
        password_create_timeout_days = password_create_timeout_seconds / (60*60*24)

        to = [send_info_to]
        fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
        subject = app.config.get("SERVICE_NAME","") + " - account created"

        try:
            if app.config.get("ENABLE_PUBLISHER_EMAIL", False):
                app_email.send_mail(to=to,
                                    fro=fro,
                                    subject=subject,
                                    template_name="email/account_created.txt",
                                    reset_url=reset_url,
                                    username=o.id,
                                    timeout_days=password_create_timeout_days,
                                    forgot_pw_url=forgot_pw_url
                )
                self.add_alert('Sent email to ' + send_info_to + ' to tell them about the new account.')
            else:
                self.add_alert('Did not email to ' + send_info_to + ' to tell them about the new account, as publisher emailing is disabled.')
            if app.config.get('DEBUG', False):
                self.add_alert('Debug mode - url for create is <a href="{url}">{url}</a>'.format(url=reset_url))
        except app_email.EmailException:
            magic = str(uuid.uuid1())
            self.add_alert('Hm, sending the account creation email didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
            if app.config.get('DEBUG', False):
                self.add_alert('Debug mode - url for create is <a href="{url}">{url}</a>'.format(url=reset_url))
            app.logger.exception('Error sending account creation email - ' + magic)

        self.add_alert('Account {username} created'.format(username=o.id))
        return o

    def _send_application_approved_email(self, journal_title, publisher_name, email, journal_contact, update_request=False):
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
                jn = journal_title #.encode('utf-8', 'replace')

                app_email.send_mail(to=to,
                                    fro=fro,
                                    subject=subject,
                                    template_name=template,
                                    journal_title=jn,
                                    publisher_name=publisher_name,
                                    journal_contact=journal_contact,
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

    def _send_contact_approved_email(self, journal_title, journal_contact, email, publisher_name, update_request=False):
        """Email the journal contact when an application is accepted """
        url_root = request.url_root
        if url_root.endswith("/"):
            url_root = url_root[:-1]

        to = [email]
        fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
        subject = app.config.get("SERVICE_NAME", "") + " - journal accepted"

        try:
            if app.config.get("ENABLE_PUBLISHER_EMAIL", False):
                template = "email/contact_application_accepted.txt"
                alert = Messages.SENT_JOURNAL_CONTACT_ACCEPTED_APPLICATION_EMAIL.format(email=to[0])
                if update_request:  # NOTE: right now, the way this is called, update request is always False.  Should deprecate and remove this code.
                    template = "email/contact_update_request_accepted.txt"
                    alert = Messages.SENT_JOURNAL_CONTACT_ACCEPTED_UPDATE_REQUEST_EMAIL.format(email=to[0])
                jn = journal_title #.encode('utf-8', 'replace')

                app_email.send_mail(to=to,
                                    fro=fro,
                                    subject=subject,
                                    template_name=template,
                                    journal_title=jn,
                                    journal_contact=journal_contact,
                                    publisher=publisher_name,
                                    url_root=url_root
                )
                self.add_alert(alert)
            else:
                alert = Messages.NOT_SENT_JOURNAL_CONTACT_ACCEPTED_APPLICATION_EMAIL.format(email=to[0])
                self.add_alert(alert)
        except Exception as e:
            magic = str(uuid.uuid1())
            self.add_alert('Hm, sending the journal contact acceptance information email didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
            app.logger.exception('Error sending accepted email to journal contact - ' + magic)

    def render_template(self, **kwargs):
        diff = None
        cj = None
        if self.source is not None:
            current_journal = self.source.current_journal
            if current_journal is not None:
                cj = models.Journal.pull(current_journal)
                if cj is not None:
                    jform = xwalk.JournalFormXWalk.obj2form(cj)
                    if "notes" in jform:
                        del jform["notes"]
                    aform = xwalk.SuggestionFormXWalk.obj2form(self.source)
                    if "notes" in aform:
                        del aform["notes"]
                    diff = self._form_diff(jform, aform)

        return super(ApplicationContext, self).render_template(
            form_diff=diff,
            current_journal=cj,
            js_functions=JAVASCRIPT_FUNCTIONS,
            **kwargs)

    def _form_diff(self, journal_form, application_form):
        diff = []
        for k, v in application_form.items():
            try:
                q = self.form[k].label
            except KeyError:
                continue
            q_num = self.renderer.question_number(k)
            if q_num is None or q_num == "":
                q_num = 0
            else:
                q_num = int(q_num)

            if k in journal_form and journal_form[k] != v:
                diff.append((k, q_num, q.text, journal_form[k], v))
            elif k not in journal_form and q_num != 0:
                diff.append((k, q_num, q.text, Messages.DIFF_TABLE_NOT_PRESENT, v))

        diff = sorted(diff, key=lambda x: x[1])
        return diff


class ApplicationFormFactory(object):
    @classmethod
    def get_form_context(cls, role=None, source=None, form_data=None):
        if role is None:
            # return PublicApplication(source=source, form_data=form_data)
            return None
        elif role == "admin":
            return ManEdApplicationReview(source=source, form_data=form_data)
        elif role == "editor":
            return EditorApplicationReview(source=source, form_data=form_data)
        elif role == "associate_editor":
            return AssEdApplicationReview(source=source, form_data=form_data)
        elif role == "publisher":
            return PublisherUpdateRequest(source=source, form_data=form_data)
        elif role == "update_request_readonly":
            return PublisherUpdateRequestReadOnly(source=source, form_data=form_data)


class JournalFormFactory(object):
    @classmethod
    def get_form_context(cls, role, source=None, form_data=None):
        if role == "admin":
            return ManEdJournalReview(source=source, form_data=form_data)
        elif role == "editor":
            return EditorJournalReview(source=source, form_data=form_data)
        elif role == "associate_editor":
            return AssEdJournalReview(source=source, form_data=form_data)
        elif role == "readonly":
            return ReadOnlyJournal(source=source, form_data=form_data)
        elif role == "bulk_edit":
            return ManEdBulkEdit(source=source, form_data=form_data)


class ManEdApplicationReview(ApplicationContext):
    """
    Managing Editor's Application Review form.  Should be used in a context where the form warrants full
    admin priviledges.  It will permit conversion of applications to journals, and assignment of owner account
    as well as assignment to editorial group.
    """
    def make_renderer(self):
        self.renderer = render.ManEdApplicationReviewRenderer()

    def set_template(self):
        self.template = "formcontext/maned_application_review.html"

    def blank_form(self):
        self.form = forms.ManEdApplicationReviewForm()
        self._set_choices()

    def data2form(self):
        self.form = forms.ManEdApplicationReviewForm(formdata=self.form_data)
        self._set_choices()
        self._expand_descriptions(FIELDS_WITH_DESCRIPTION)
        self._expand_url_descriptions(URL_FIELDS)

    def source2form(self):
        self.form = forms.ManEdApplicationReviewForm(data=xwalk.SuggestionFormXWalk.obj2form(self.source))
        self._set_choices()
        self._expand_descriptions(FIELDS_WITH_DESCRIPTION)
        self._expand_url_descriptions(URL_FIELDS)
        if self.source.application_status == constants.APPLICATION_STATUS_ACCEPTED:
            self.info = ACC_MSG

    def pre_validate(self):
        # Editor field is populated in JS after page load - check the selected editor is actually in that editor group
        self._validate_editor_field()

    def form2target(self):
        self.target = xwalk.SuggestionFormXWalk.form2obj(self.form)

    def patch_target(self):
        if self.source is None:
            raise FormContextException("You cannot patch a target from a non-existent source")

        self._carry_fixed_aspects()
        self._merge_notes_forward(allow_delete=True)

        # NOTE: this means you can't unset an owner once it has been set.  But you can change it.
        if (self.target.owner is None or self.target.owner == "") and (self.source.owner is not None):
            self.target.set_owner(self.source.owner)

    def finalise(self):
        # FIXME: this first one, we ought to deal with outside the form context, but for the time being this
        # can be carried over from the old implementation

        if self.source is None:
            raise FormContextException("You cannot edit a not-existent application")
        if self.source.application_status == constants.APPLICATION_STATUS_ACCEPTED:
            raise FormContextException("You cannot edit applications which have been accepted into DOAJ.")

        # if we are allowed to finalise, kick this up to the superclass
        super(ManEdApplicationReview, self).finalise()

        # FIXME: may want to factor this out of the suggestionformxwalk
        # If we have changed the editors assinged to this application, let them know.
        is_editor_group_changed = xwalk.SuggestionFormXWalk.is_new_editor_group(self.form, self.source)
        is_associate_editor_changed = xwalk.SuggestionFormXWalk.is_new_editor(self.form, self.source)

        # record the event in the provenance tracker
        models.Provenance.make(current_user, "edit", self.target)

        # delayed import of the DOAJ BLL
        from portality.bll.doaj import DOAJ
        applicationService = DOAJ.applicationService()

        # if this application is being accepted, then do the conversion to a journal
        if self.target.application_status == constants.APPLICATION_STATUS_ACCEPTED:
            # remember whether this was an update request or not
            is_update_request = self.target.current_journal is not None

            j = applicationService.accept_application(self.target, current_user._get_current_object())
            # record the url the journal is available at in the admin are and alert the user
            jurl = url_for("doaj.toc", identifier=j.toc_id)
            if self.source.current_journal is not None:
                self.add_alert('<a href="{url}" target="_blank">Existing journal updated</a>.'.format(url=jurl))
            else:
                self.add_alert('<a href="{url}" target="_blank">New journal created</a>.'.format(url=jurl))

            # create the user account for the owner and send the notification email
            try:
                owner = self._create_account_on_suggestion_approval(self.target, j)
                names = []
                for contact in j.contacts():
                    names.append(contact.get("name"))
                journal_contacts = ", ".join(names)

                # for all acceptances, send an email to the owner of the journal
                self._send_application_approved_email(j.bibjson().title, owner.name, owner.email, journal_contacts, self.source.current_journal is not None)

                # in the case of a new application, also send emails to the journal contacts
                if not is_update_request:
                    for contact in j.contacts():
                        self._send_contact_approved_email(j.bibjson().title, contact.get("name"), contact.get("email"), owner.name, self.source.current_journal is not None)
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
                    send_report = emails.send_publisher_reject_email(self.target, update_request=is_update_request, send_to_owner=True, send_to_suggester=False)
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

    def render_template(self, **kwargs):
        if self.source is None:
            raise FormContextException("You cannot edit a not-existent application")

        return super(ManEdApplicationReview, self).render_template(
            lcc_jstree=json.dumps(lcc_jstree),
            subjectstr=self._subjects2str(self.source.bibjson().subjects()),
            **kwargs)

    def _set_choices(self):
        self.form.application_status.choices = choices.Choices.choices_for_status('admin', self.source.application_status)

        # The first time the form is rendered, it needs to populate the editor drop-down from saved group
        egn = self.form.editor_group.data
        self._populate_editor_field(egn)


class EditorApplicationReview(ApplicationContext):
    """
    Editors Application Review form.  This should be used in a context where an editor who owns an editorial group
    is accessing an application.  This prevents re-assignment of Editorial group, but permits assignment of associate
    editor.  It also permits change in application state, except to "accepted"; therefore this form context cannot
    be used to create journals from applications. Deleting notes is not allowed, but adding is.
    """
    def make_renderer(self):
        self.renderer = render.EditorApplicationReviewRenderer()
        self.renderer.set_disabled_fields(["editor_group"])

    def set_template(self):
        self.template = "formcontext/editor_application_review.html"

    def blank_form(self):
        self.form = forms.EditorApplicationReviewForm()
        self._set_choices()

    def data2form(self):
        self.form = forms.EditorApplicationReviewForm(formdata=self.form_data)
        self._set_choices()
        self._expand_descriptions(FIELDS_WITH_DESCRIPTION)
        self._expand_url_descriptions(URL_FIELDS)

    def source2form(self):
        self.form = forms.EditorApplicationReviewForm(data=xwalk.SuggestionFormXWalk.obj2form(self.source))
        self._set_choices()
        self._expand_descriptions(FIELDS_WITH_DESCRIPTION)
        self._expand_url_descriptions(URL_FIELDS)
        editor_choices = list(sum(choices.Choices.application_status('editor'), ()))       # flattens the list of tuples
        if self.source.application_status not in editor_choices:
            self.info = SCOPE_MSG.format(self.source.application_status)

        if self.source.application_status == constants.APPLICATION_STATUS_ACCEPTED:
            self.info = ACC_MSG                                     # This is after so we can supersede the last message

    def pre_validate(self):
        self.form.editor_group.data = self.source.editor_group
        if "application_status" in self.renderer.disabled_fields:
            self.form.application_status.data = constants.APPLICATION_STATUS_ACCEPTED

    def form2target(self):
        self.target = xwalk.SuggestionFormXWalk.form2obj(self.form)

    def patch_target(self):
        if self.source is None:
            raise FormContextException("You cannot patch a target from a non-existent source")

        self._carry_fixed_aspects()
        self._merge_notes_forward()
        self.target.set_owner(self.source.owner)
        self.target.set_editor_group(self.source.editor_group)
        self._carry_continuations()

    def finalise(self):
        # FIXME: this first one, we ought to deal with outside the form context, but for the time being this
        # can be carried over from the old implementation
        if self.source is None:
            raise FormContextException("You cannot edit a not-existent application")
        if self.source.application_status == constants.APPLICATION_STATUS_ACCEPTED:
            raise FormContextException("You cannot edit applications which have been accepted into DOAJ.")

        # if we are allowed to finalise, kick this up to the superclass
        super(EditorApplicationReview, self).finalise()

        # Check the status change is valid
        choices.Choices.validate_status_change('editor', self.source.application_status, self.target.application_status)

        # FIXME: may want to factor this out of the suggestionformxwalk
        new_associate_assigned = xwalk.SuggestionFormXWalk.is_new_editor(self.form, self.source)

        # Save the target
        self.target.set_last_manual_update()
        self.target.save()

        # record the event in the provenance tracker
        models.Provenance.make(current_user, "edit", self.target)

        # if we need to email the associate because they have just been assigned, handle that here.
        if new_associate_assigned:
            try:
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
                self.add_alert('An email has been sent to notify the assigned associate editor of the change in status.')
            except AttributeError as e:
                magic = str(uuid.uuid1())
                self.add_alert('Couldn\'t find a recipient for this email - check an associate editor is assigned. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
                app.logger.exception('No associate editor recipient for failed review email - ' + magic)
            except app_email.EmailException:
                magic = str(uuid.uuid1())
                self.add_alert('Sending the failed review email to associate editor didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
                app.logger.exception('Error sending failed review email to associate editor - ' + magic)

        # email managing editors if the application was newly set to 'ready'
        if self.source.application_status != constants.APPLICATION_STATUS_READY and self.target.application_status == constants.APPLICATION_STATUS_READY:
            # Tell the ManEds who has made the status change - the editor in charge of the group
            editor_group_name = self.target.editor_group
            editor_group_id = models.EditorGroup.group_exists_by_name(name=editor_group_name)
            editor_group = models.EditorGroup.pull(editor_group_id)
            editor_acc = editor_group.get_editor_account()

            # record the event in the provenance tracker
            models.Provenance.make(current_user, "status:ready", self.target)

            editor_id = editor_acc.id
            try:
                emails.send_admin_ready_email(self.target, editor_id=editor_id)
                self.add_alert('A confirmation email has been sent to the Managing Editors.')
            except app_email.EmailException:
                magic = str(uuid.uuid1())
                self.add_alert('Hm, sending the ready status to managing editors didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
                app.logger.exception('Error sending ready status email to managing editors - ' + magic)

    def render_template(self, **kwargs):
        if self.source is None:
            raise FormContextException("You cannot edit a not-existent application")

        return super(EditorApplicationReview, self).render_template(
            lcc_jstree=json.dumps(lcc_jstree),
            subjectstr=self._subjects2str(self.source.bibjson().subjects()),
            **kwargs)

    def _set_choices(self):
        if self.source is None:
            raise FormContextException("You cannot set choices for a non-existent source")
        if self.form.application_status.data == constants.APPLICATION_STATUS_ACCEPTED:
            self.form.application_status.choices = choices.Choices.application_status("accepted")
            self.renderer.set_disabled_fields(self.renderer.disabled_fields + ["application_status"])
        else:
            try:
                # Assign the choices to the form
                self.form.application_status.choices = choices.Choices.choices_for_status('editor', self.source.application_status)
            except ValueError:
                # If the current status isn't in the editor's status list, it must be out of bounds. Show it greyed out.
                self.form.application_status.choices = choices.Choices.application_status("admin")
                self.renderer.set_disabled_fields(self.renderer.disabled_fields + ["application_status"])

        # get the editor group from the source because it isn't in the form
        egn = self.source.editor_group
        self._populate_editor_field(egn)


class AssEdApplicationReview(ApplicationContext):
    """
    Associate Editors Application Review form. This is to be used in a context where an associate editor (fewest rights)
    needs to access an application for review. This editor cannot change the editorial group or the assigned editor.
    They also cannot change the owner of the application. They cannot set an application to "Accepted" so this form can't
    be used to create a journal from an application. They cannot delete, only add notes.
    """
    def make_renderer(self):
        self.renderer = render.AssEdApplicationReviewRenderer()

    def set_template(self):
        self.template = "formcontext/assed_application_review.html"

    def blank_form(self):
        self.form = forms.AssEdApplicationReviewForm()
        self._set_choices()

    def data2form(self):
        self.form = forms.AssEdApplicationReviewForm(formdata=self.form_data)
        self._set_choices()
        self._expand_descriptions(FIELDS_WITH_DESCRIPTION)
        self._expand_url_descriptions(URL_FIELDS)

    def source2form(self):
        self.form = forms.AssEdApplicationReviewForm(data=xwalk.SuggestionFormXWalk.obj2form(self.source))
        self._set_choices()
        self._expand_descriptions(FIELDS_WITH_DESCRIPTION)
        self._expand_url_descriptions(URL_FIELDS)

        associate_editor_choices = list(sum(choices.Choices.application_status(), ()))     # flattens the list of tuples
        if self.source.application_status not in associate_editor_choices:
            self.info = SCOPE_MSG.format(self.source.application_status)

        if self.source.application_status == constants.APPLICATION_STATUS_ACCEPTED:
            self.info = ACC_MSG                                     # This is after so we can supersede the last message

    def pre_validate(self):
        if "application_status" in self.renderer.disabled_fields:
            self.form.application_status.data = constants.APPLICATION_STATUS_ACCEPTED

    def form2target(self):
        self.target = xwalk.SuggestionFormXWalk.form2obj(self.form)

    def patch_target(self):
        if self.source is None:
            raise FormContextException("You cannot patch a target from a non-existent source")

        self._carry_fixed_aspects()
        self._merge_notes_forward()
        self.target.set_owner(self.source.owner)
        self.target.set_editor_group(self.source.editor_group)
        self.target.set_editor(self.source.editor)
        self.target.set_seal(self.source.has_seal())
        self._carry_continuations()

    def finalise(self):
        # FIXME: this first one, we ought to deal with outside the form context, but for the time being this
        # can be carried over from the old implementation
        if self.source is None:
            raise FormContextException("You cannot edit a not-existent application")
        if self.source.application_status == constants.APPLICATION_STATUS_ACCEPTED:
            raise FormContextException("You cannot edit applications which have been accepted into DOAJ.")

        # if we are allowed to finalise, kick this up to the superclass
        super(AssEdApplicationReview, self).finalise()

        # Check the status change is valid
        choices.Choices.validate_status_change('associate', self.source.application_status, self.target.application_status)

        # Save the target
        self.target.set_last_manual_update()
        self.target.save()

        # record the event in the provenance tracker
        models.Provenance.make(current_user, "edit", self.target)

        # inform publisher if this was set to 'in progress' from 'pending'
        if self.source.application_status == constants.APPLICATION_STATUS_PENDING and self.target.application_status == constants.APPLICATION_STATUS_IN_PROGRESS:
            if app.config.get("ENABLE_PUBLISHER_EMAIL", False):
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
            models.Provenance.make(current_user, "status:completed", self.target)

            try:
                emails.send_editor_completed_email(self.target)
                self.add_alert('A confirmation email has been sent to notify the editor of the change in status.')
            except app_email.EmailException:
                magic = str(uuid.uuid1())
                self.add_alert('Hm, sending the ready status to editor email didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
                app.logger.exception('Error sending completed status email to editor - ' + magic)

    def render_template(self, **kwargs):
        if self.source is None:
            raise FormContextException("You cannot edit a not-existent application")

        return super(AssEdApplicationReview, self).render_template(
            lcc_jstree=json.dumps(lcc_jstree),
            subjectstr=self._subjects2str(self.source.bibjson().subjects()),
            **kwargs)

    def _set_choices(self):
        if self.form.application_status.data == constants.APPLICATION_STATUS_ACCEPTED:
            self.form.application_status.choices = choices.Choices.application_status("accepted")
            self.renderer.set_disabled_fields(self.renderer.disabled_fields + ["application_status"])
        else:
            try:
                # Assign the choices to the form
                self.form.application_status.choices = choices.Choices.choices_for_status('associate_editor', self.source.application_status)
            except ValueError:
                # If the current status isn't in the associate editor's status list, it must be out of bounds. Show it greyed out.
                self.form.application_status.choices = choices.Choices.application_status("admin")
                self.renderer.set_disabled_fields(self.renderer.disabled_fields + ["application_status"])


class PublisherUpdateRequest(ApplicationContext):
    def make_renderer(self):
        self.renderer = render.PublisherUpdateRequestRenderer()

    def set_template(self):
        self.template = "formcontext/publisher_update_request.html"

    def blank_form(self):
        self.form = forms.PublisherUpdateRequestForm()

    def data2form(self):
        self.form = forms.PublisherUpdateRequestForm(formdata=self.form_data)
        self._expand_descriptions(FIELDS_WITH_DESCRIPTION)
        self._expand_url_descriptions(URL_FIELDS)
        self._disable_fields()

    def source2form(self):
        self.form = forms.PublisherUpdateRequestForm(data=xwalk.SuggestionFormXWalk.obj2form(self.source))
        self._expand_descriptions(FIELDS_WITH_DESCRIPTION)
        self._expand_url_descriptions(URL_FIELDS)
        self._disable_fields()

    def pre_validate(self):
        if self.source is None:
            raise FormContextException("You cannot validate a form from a non-existent source")

        # carry forward the disabled fields
        bj = self.source.bibjson()
        contact = self.source.contact

        self.form.title.data = bj.title
        self.form.alternative_title.data = bj.alternative_title

        pissn = bj.get_one_identifier(bj.P_ISSN)
        if pissn == "": pissn = None
        self.form.pissn.data = pissn

        eissn = bj.get_one_identifier(bj.E_ISSN)
        if eissn == "": eissn = None
        self.form.eissn.data = eissn

        if len(contact) == 0:
            # this will cause a validation failure if the form does not provide them
            return

        # we copy across the contacts if they are necessary.  The contact details are conditionally
        # disabled, so they /may/ be set
        if "contact_name" in self.renderer.disabled_fields:
            self.form.contact_name.data = contact.get("name")
        if "contact_email" in self.renderer.disabled_fields:
            self.form.contact_email.data = contact.get("email")
        if "confirm_contact_email" in self.renderer.disabled_fields:
            self.form.confirm_contact_email.data = contact.get("email")

    def form2target(self):
        self.target = xwalk.SuggestionFormXWalk.form2obj(self.form)

    def patch_target(self):
        if self.source is None:
            raise FormContextException("You cannot patch a target from a non-existent source")

        self._carry_subjects_and_seal()
        self._carry_fixed_aspects()
        self._merge_notes_forward()
        self.target.set_owner(self.source.owner)
        self.target.set_editor_group(self.source.editor_group)
        self.target.set_editor(self.source.editor)
        self._carry_continuations()

        # set the suggester to the account owner
        acc = models.Account.pull(self.target.owner)
        if acc is not None:
            self.target.set_suggester(acc.name, acc.email)

        # we carry this over for completeness, although it will be overwritten in the finalise() method
        self.target.set_application_status(self.source.application_status)

    def finalise(self, save_target=True, email_alert=True):
        # FIXME: this first one, we ought to deal with outside the form context, but for the time being this
        # can be carried over from the old implementation
        if self.source is None:
            raise FormContextException("You cannot edit a not-existent application")

        # if we are allowed to finalise, kick this up to the superclass
        super(PublisherUpdateRequest, self).finalise()

        # set the status to update_request (if not already)
        self.target.set_application_status(constants.APPLICATION_STATUS_UPDATE_REQUEST)

        # Save the target
        self.target.set_last_manual_update()
        if save_target:
            saved = self.target.save()
            if saved is None:
                raise FormContextException("Save on application failed")

        # obtain the related journal, and attach the current application id to it
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
                        raise FormContextException("Save on journal failed")
            else:
                self.target.remove_current_journal()

        # email the publisher to tell them we received their update request
        if email_alert:
            try:
                self._send_received_email()
            except app_email.EmailException as e:
                self.add_alert("We were unable to send you an email confirmation - possible problem with your email address")
                app.logger.exception('Error sending reapplication received email to publisher')

    def render_template(self, **kwargs):
        if self.source is None:
            raise FormContextException("You cannot edit a not-existent application")

        return super(PublisherUpdateRequest, self).render_template(**kwargs)

    def _carry_subjects_and_seal(self):
        # carry over the subjects
        source_subjects = self.source.bibjson().subjects()
        self.target.bibjson().set_subjects(source_subjects)

        # carry over the seal
        self.target.set_seal(self.source.has_seal())

    def _disable_fields(self):
        if self.source is None:
            raise FormContextException("You cannot disable fields on a not-existent application")

        disable = ["title", "alternative_title", "pissn", "eissn"] # these are always disabled

        # contact fields are only disabled if they already have content in source
        contact = self.source.contact
        if contact.get("name"):
            disable.append("contact_name")
        if contact.get("email"):
            disable += ["contact_email", "confirm_contact_email"]

        self.renderer.set_disabled_fields(disable)

    def _send_received_email(self):
        acc = models.Account.pull(self.target.owner)
        if acc is None:
            self.add_alert("Unable to locate account for specified owner")
            return

        journal_name = self.target.bibjson().title #.encode('utf-8', 'replace')

        to = [acc.email]
        fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
        subject = app.config.get("SERVICE_NAME","") + " - update request received"

        try:
            if app.config.get("ENABLE_PUBLISHER_EMAIL", False):
                app_email.send_mail(to=to,
                                    fro=fro,
                                    subject=subject,
                                    template_name="email/publisher_update_request_received.txt",
                                    journal_name=journal_name,
                                    username=self.target.owner
                )
                self.add_alert('A confirmation email has been sent to ' + acc.email + '.')
        except app_email.EmailException as e:
            magic = str(uuid.uuid1())
            self.add_alert('Hm, sending the "update request received" email didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
            app.logger.error(magic + "\n" + repr(e))
            raise e


class PublisherUpdateRequestReadOnly(PrivateContext):
    """
    Read Only Application form for publishers. Nothing can be changed. Useful to show publishers what they
    currently have submitted for review
    """
    def make_renderer(self):
        self.renderer = render.PublisherUpdateRequestReadOnlyRenderer()

    def set_template(self):
        self.template = "formcontext/readonly_application.html"

    def blank_form(self):
        self.form = forms.PublisherUpdateRequestForm()
        self.renderer.disable_all_fields(False)
        # self._set_choices()

    def data2form(self):
        self.form = forms.PublisherUpdateRequestForm(formdata=self.form_data)
        # self._set_choices()
        self._expand_descriptions(FIELDS_WITH_DESCRIPTION)
        self._expand_url_descriptions(URL_FIELDS)
        self.renderer.disable_all_fields(False)

    def source2form(self):
        self.form = forms.PublisherUpdateRequestForm(data=xwalk.JournalFormXWalk.obj2form(self.source))
        # self._set_choices()
        self._expand_descriptions(FIELDS_WITH_DESCRIPTION)
        self._expand_url_descriptions(URL_FIELDS)
        self.renderer.set_disabled_fields(["digital_archiving_policy"])
        # self.renderer.disable_all_fields(True)

    def form2target(self):
        pass  # you can't edit objects using this form

    def patch_target(self):
        pass  # you can't edit objects using this form

    def finalise(self):
        raise FormContextException("You cannot edit applications using the read-only form")

    """
    def render_template(self, **kwargs):
        if self.source is None:
            raise FormContextException("You cannot view a not-existent journal")

        return super(ReadOnlyJournal, self).render_template(
            lcc_jstree=json.dumps(lcc_jstree),
            subjectstr=self._subjects2str(self.source.bibjson().subjects()),
            **kwargs
        )
    """
    """
    def _set_choices(self):
        # no application status (this is a journal) or editorial info (it's not even in the form) to set
        pass
    """

### Journal form contexts ###

class ManEdJournalReview(PrivateContext):
    """
    Managing Editor's Journal Review form.  Should be used in a context where the form warrants full
    admin privileges.  It will permit doing every action.
    """
    def make_renderer(self):
        self.renderer = render.ManEdJournalReviewRenderer()

    def set_template(self):
        self.template = "formcontext/maned_journal_review.html"

    def render_template(self, **kwargs):
        if self.source is None:
            raise FormContextException("You cannot edit a not-existent journal")

        return super(ManEdJournalReview, self).render_template(
            lcc_jstree=json.dumps(lcc_jstree),
            subjectstr=self._subjects2str(self.source.bibjson().subjects()),
            **kwargs)

    def blank_form(self):
        self.form = forms.ManEdApplicationReviewForm()
        self._set_choices()

    def data2form(self):
        self.form = forms.ManEdJournalReviewForm(formdata=self.form_data)
        self._set_choices()
        self._expand_descriptions(FIELDS_WITH_DESCRIPTION)
        self._expand_url_descriptions(URL_FIELDS)

    def source2form(self):
        self.form = forms.ManEdJournalReviewForm(data=xwalk.JournalFormXWalk.obj2form(self.source))
        self._set_choices()
        self._expand_descriptions(FIELDS_WITH_DESCRIPTION)
        self._expand_url_descriptions(URL_FIELDS)

    def pre_validate(self):
        # Editor field is populated in JS after page load - check the selected editor is actually in that editor group
        self._validate_editor_field()

    def form2target(self):
        self.target = xwalk.JournalFormXWalk.form2obj(self.form)

    def patch_target(self):
        if self.source is None:
            raise FormContextException("You cannot patch a target from a non-existent source")

        self._carry_fixed_aspects()

        # NOTE: this means you can't unset an owner once it has been set.  But you can change it.
        if (self.target.owner is None or self.target.owner == "") and (self.source.owner is not None):
            self.target.set_owner(self.source.owner)

        self._merge_notes_forward(allow_delete=True)

    def _set_choices(self):
        # The first time this is rendered, it needs to populate the editor drop-down from saved group
        egn = self.form.editor_group.data
        self._populate_editor_field(egn)

    def finalise(self):
        # FIXME: this first one, we ought to deal with outside the form context, but for the time being this
        # can be carried over from the old implementation

        if self.source is None:
            raise FormContextException("You cannot edit a not-existent journal")

        # if we are allowed to finalise, kick this up to the superclass
        super(ManEdJournalReview, self).finalise()

        # FIXME: may want to factor this out of the suggestionformxwalk
        # If we have changed the editors assinged to this application, let them know.
        is_editor_group_changed = xwalk.JournalFormXWalk.is_new_editor_group(self.form, self.source)
        is_associate_editor_changed = xwalk.JournalFormXWalk.is_new_editor(self.form, self.source)

        # Save the target
        self.target.set_last_manual_update()
        self.target.save()

        # if we need to email the editor and/or the associate, handle those here
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


class ManEdBulkEdit(PrivateContext):
    """
    Managing Editor's Journal Review form.  Should be used in a context where the form warrants full
    admin privileges.  It will permit doing every action.
    """
    def make_renderer(self):
        self.renderer = render.ManEdJournalBulkEditRenderer()

    def set_template(self):
        self.template = "formcontext/maned_journal_bulk_edit.html"

    def blank_form(self):
        self.form = forms.ManEdBulkEditJournalForm()

    def data2form(self):
        self.form = forms.ManEdBulkEditJournalForm(formdata=self.form_data)
        self._expand_descriptions(FIELDS_WITH_DESCRIPTION)
        self._expand_url_descriptions(URL_FIELDS)


class EditorJournalReview(PrivateContext):
    """
    Editors Journal Review form.  This should be used in a context where an editor who owns an editorial group
    is accessing a journal.  This prevents re-assignment of Editorial group, but permits assignment of associate
    editor.
    """
    def make_renderer(self):
        self.renderer = render.EditorJournalReviewRenderer()
        self.renderer.set_disabled_fields(["editor_group"])

    def set_template(self):
        self.template = "formcontext/editor_journal_review.html"

    def render_template(self, **kwargs):
        if self.source is None:
            raise FormContextException("You cannot edit a not-existent journal")

        return super(EditorJournalReview, self).render_template(
            lcc_jstree=json.dumps(lcc_jstree),
            subjectstr=self._subjects2str(self.source.bibjson().subjects()),
            **kwargs)

    def blank_form(self):
        self.form = forms.EditorJournalReviewForm()
        self._set_choices()

    def data2form(self):
        self.form = forms.EditorJournalReviewForm(formdata=self.form_data)
        self._set_choices()
        self._expand_descriptions(FIELDS_WITH_DESCRIPTION)
        self._expand_url_descriptions(URL_FIELDS)

    def source2form(self):
        self.form = forms.EditorJournalReviewForm(data=xwalk.JournalFormXWalk.obj2form(self.source))
        self._set_choices()
        self._expand_descriptions(FIELDS_WITH_DESCRIPTION)
        self._expand_url_descriptions(URL_FIELDS)

    def form2target(self):
        self.target = xwalk.JournalFormXWalk.form2obj(self.form)

    def patch_target(self):
        if self.source is None:
            raise FormContextException("You cannot patch a target from a non-existent source")

        self._carry_fixed_aspects()
        self.target.set_owner(self.source.owner)
        self.target.set_editor_group(self.source.editor_group)
        self._merge_notes_forward()
        self._carry_continuations()

    def pre_validate(self):
        self.form.editor_group.data = self.source.editor_group

    def _set_choices(self):
        if self.source is None:
            raise FormContextException("You cannot set choices for a non-existent source")

        # get the editor group from the source because it isn't in the form
        egn = self.source.editor_group
        self._populate_editor_field(egn)

    def finalise(self):
        # FIXME: this first one, we ought to deal with outside the form context, but for the time being this
        # can be carried over from the old implementation

        if self.source is None:
            raise FormContextException("You cannot edit a not-existent journal")

        # if we are allowed to finalise, kick this up to the superclass
        super(EditorJournalReview, self).finalise()

        # FIXME: may want to factor this out of the suggestionformxwalk
        email_associate = xwalk.SuggestionFormXWalk.is_new_editor(self.form, self.source)

        # Save the target
        self.target.set_last_manual_update()
        self.target.save()

        # if we need to email the associate, handle that here.
        if email_associate:
            try:
                emails.send_assoc_editor_email(self.target)
            except app_email.EmailException:
                self.add_alert("Problem sending email to associate editor - probably address is invalid")
                app.logger.exception('Error sending assignment email to associate.')


class AssEdJournalReview(PrivateContext):
    """
    Associate Editors Journal Review form. This is to be used in a context where an associate editor (fewest rights)
    needs to access a journal for review. This editor cannot change the editorial group or the assigned editor.
    They also cannot change the owner of the journal. They cannot delete, only add notes.
    """
    def make_renderer(self):
        self.renderer = render.AssEdJournalReviewRenderer()

    def set_template(self):
        self.template = "formcontext/assed_journal_review.html"

    def blank_form(self):
        self.form = forms.AssEdJournalReviewForm()
        self._set_choices()

    def data2form(self):
        self.form = forms.AssEdJournalReviewForm(formdata=self.form_data)
        self._set_choices()
        self._expand_descriptions(FIELDS_WITH_DESCRIPTION)
        self._expand_url_descriptions(URL_FIELDS)

    def source2form(self):
        self.form = forms.AssEdJournalReviewForm(data=xwalk.JournalFormXWalk.obj2form(self.source))
        self._set_choices()
        self._expand_descriptions(FIELDS_WITH_DESCRIPTION)
        self._expand_url_descriptions(URL_FIELDS)

    def form2target(self):
        self.target = xwalk.JournalFormXWalk.form2obj(self.form)

    def patch_target(self):
        if self.source is None:
            raise FormContextException("You cannot patch a target from a non-existent source")

        self._carry_fixed_aspects()
        self._merge_notes_forward()
        self.target.set_owner(self.source.owner)
        self.target.set_editor_group(self.source.editor_group)
        self.target.set_editor(self.source.editor)
        self._carry_continuations()

    def finalise(self):
        # FIXME: this first one, we ought to deal with outside the form context, but for the time being this
        # can be carried over from the old implementation
        if self.source is None:
            raise FormContextException("You cannot edit a not-existent journal")

        # if we are allowed to finalise, kick this up to the superclass
        super(AssEdJournalReview, self).finalise()

        # Save the target
        self.target.set_last_manual_update()
        self.target.save()

    def render_template(self, **kwargs):
        if self.source is None:
            raise FormContextException("You cannot edit a not-existent journal")

        return super(AssEdJournalReview, self).render_template(
            lcc_jstree=json.dumps(lcc_jstree),
            subjectstr=self._subjects2str(self.source.bibjson().subjects()),
            **kwargs
        )

    def _set_choices(self):
        # no application status (this is a journal) or editorial info (it's not even in the form) to set
        pass


class ReadOnlyJournal(PrivateContext):
    """
    Read Only Journal form. Nothing can be changed. Useful for reviewing a journal and an application
    (or update request) side by side in 2 browser windows or tabs.
    """
    def make_renderer(self):
        self.renderer = render.ReadOnlyJournalRenderer()

    def set_template(self):
        self.template = "formcontext/readonly_journal.html"

    def blank_form(self):
        self.form = forms.ReadOnlyJournalForm()
        self._set_choices()

    def data2form(self):
        self.form = forms.ReadOnlyJournalForm(formdata=self.form_data)
        self._set_choices()
        self._expand_descriptions(FIELDS_WITH_DESCRIPTION)
        self._expand_url_descriptions(URL_FIELDS)

    def source2form(self):
        self.form = forms.ReadOnlyJournalForm(data=xwalk.JournalFormXWalk.obj2form(self.source))
        self._set_choices()
        self._expand_descriptions(FIELDS_WITH_DESCRIPTION)
        self._expand_url_descriptions(URL_FIELDS)

    def form2target(self):
        pass  # you can't edit objects using this form

    def patch_target(self):
        pass  # you can't edit objects using this form

    def finalise(self):
        raise FormContextException("You cannot edit journals using the read-only form")

    def render_template(self, **kwargs):
        if self.source is None:
            raise FormContextException("You cannot view a not-existent journal")

        return super(ReadOnlyJournal, self).render_template(
            lcc_jstree=json.dumps(lcc_jstree),
            subjectstr=self._subjects2str(self.source.bibjson().subjects()),
            **kwargs
        )

    def _set_choices(self):
        # no application status (this is a journal) or editorial info (it's not even in the form) to set
        pass
