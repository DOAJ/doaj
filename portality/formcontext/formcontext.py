from flask import render_template, url_for, request
import json, uuid
from datetime import datetime

from portality.formcontext import forms, xwalk, render, choices
from portality.lcc import lcc_jstree
from portality import models, app_email, util
from portality.core import app

class FormContextException(Exception):
    pass

class FormContext(object):
    def __init__(self, form_data=None, source=None):
        # initialise our core properties
        self._source = source
        self._target = None
        self._form_data = form_data
        self._form = None
        self._renderer = None
        self._template = None
        self._alert = []

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

    def finalise(self):
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
            if self.renderer is not None:
                self.renderer.set_error_fields(error_fields)

        return valid

    @property
    def errors(self):
        f = self.form
        if f is not None:
            return f.errors
        return False

    def render_template(self, **kwargs):
        return render_template(self.template, form_context=self, **kwargs)

    def render_field_group(self, field_group_name=None):
        return self.renderer.render_field_group(self, field_group_name)


class PrivateContext(FormContext):
    def _expand_descriptions(self, fields):
        # add the contents of a few fields to their descriptions since select2 autocomplete
        # would otherwise obscure the full values
        for field in fields:
            if self.form[field].data:
                if not self.form[field].description:
                    self.form[field].description = 'Full contents: ' + self.form[field].data
                else:
                    self.form[field].description += '<br><br>Full contents: ' + self.form[field].data

    def _carry_fixed_aspects(self):
        if self.source is None:
            raise FormContextException("Cannot carry data from a non-existent source")

        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        # copy over any important fields from the previous version of the object
        created_date = self.source.created_date if self.source.created_date else now
        self.target.set_created(created_date)
        self.target.data['id'] = self.source.data['id']

        if self.source.current_application:
            self.target.set_current_application(self.source.current_application)

        if self.source.last_reapplication:
            self.target.set_last_reapplication(self.source.last_reapplication)

        try:
            if self.source.current_journal:
                self.target.set_current_journal(self.source.current_journal)
        except AttributeError:
            # this means that the source doesn't know about current_journals, which is fine
            pass

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
        tnotes = self.target.notes()
        snotes = self.source.notes()

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

    @staticmethod
    def _send_editor_group_email(suggestion):
        eg = models.EditorGroup.pull_by_key("name", suggestion.editor_group)
        if eg is None:
            return
        editor = models.Account.pull(eg.editor)

        url_root = app.config.get("BASE_URL")
        to = [editor.email]
        fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
        subject = app.config.get("SERVICE_NAME","") + " - new journal assigned to your group"

        app_email.send_mail(to=to,
                            fro=fro,
                            subject=subject,
                            template_name="email/suggestion_assigned_group.txt",
                            editor=editor.id.encode('utf-8', 'replace'),
                            journal_name=suggestion.bibjson().title.encode('utf-8', 'replace'),
                            url_root=url_root
                            )

    @staticmethod
    def _send_editor_email(suggestion):
        editor = models.Account.pull(suggestion.editor)
        eg = models.EditorGroup.pull_by_key("name", suggestion.editor_group)

        url_root = app.config.get("BASE_URL")
        to = [editor.email]
        fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
        subject = app.config.get("SERVICE_NAME","") + " - new journal assigned to you"

        app_email.send_mail(to=to,
                            fro=fro,
                            subject=subject,
                            template_name="email/suggestion_assigned_editor.txt",
                            editor=editor.id.encode('utf-8', 'replace'),
                            journal_name=suggestion.bibjson().title.encode('utf-8', 'replace'),
                            group_name=eg.name.encode("utf-8", "replace"),
                            url_root=url_root
                            )

    def _create_account_on_suggestion_approval(self, suggestion, journal):
        o = models.Account.pull(suggestion.owner)
        if o:
            self.add_alert('Account {username} already exists, so simply associating the new journal with it.'.format(username=o.id))
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
            if app.config.get('DEBUG',False):
                self.add_alert('Debug mode - url for create is <a href="{url}">{url}</a>'.format(url=reset_url))
        except Exception as e:
            magic = str(uuid.uuid1())
            self.add_alert('Hm, sending the account creation email didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
            if app.config.get('DEBUG',False):
                self.add_alert('Debug mode - url for create is <a href="{url}">{url}</a>'.format(url=reset_url))
            app.logger.error(magic + "\n" + repr(e))
            raise e

        self.add_alert('Account {username} created'.format(username=o.id))
        return o

    def _send_suggestion_approved_email(self, journal_name, email):
        url_root = request.url_root
        if url_root.endswith("/"):
            url_root = url_root[:-1]

        to = [email]
        fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
        subject = app.config.get("SERVICE_NAME","") + " - journal accepted"

        try:
            if app.config.get("ENABLE_PUBLISHER_EMAIL", False):
                app_email.send_mail(to=to,
                                    fro=fro,
                                    subject=subject,
                                    template_name="email/suggestion_accepted.txt",
                                    journal_name=journal_name.encode('utf-8', 'replace'),
                                    url_root=url_root
                )
                self.add_alert('Sent email to ' + email + ' to tell them about their journal getting accepted into DOAJ.')
            else:
                self.add_alert('Did not send email to ' + email + ' to tell them about their journal getting accepted into DOAJ, as publisher emails are disabled.')
        except Exception as e:
            magic = str(uuid.uuid1())
            self.add_alert('Hm, sending the journal acceptance information email didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
            app.logger.error(magic + "\n" + repr(e))
            raise e


class ApplicationFormFactory(object):
    @classmethod
    def get_form_context(cls, role=None, source=None, form_data=None):
        if role is None:
            return PublicApplication(source=source, form_data=form_data)
        elif role == "admin":
            return ManEdApplicationReview(source=source, form_data=form_data)
        elif role == "editor":
            return EditorApplicationReview(source=source, form_data=form_data)
        elif role == "associate_editor":
            return AssEdApplicationReview(source=source, form_data=form_data)
        elif role == "publisher":
            return PublisherReApplication(source=source, form_data=form_data)
        elif role == "csv":
            return PublisherCsvReApplication(source=source, form_data=form_data)

class JournalFormFactory(object):
    @classmethod
    def get_form_context(cls, role, source=None, form_data=None):
        if role == "admin":
            return ManEdJournalReview(source=source, form_data=form_data)
        elif role == "editor":
            return EditorJournalReview(source=source, form_data=form_data)
        elif role == "associate_editor":
            return AssEdJournalReview(source=source, form_data=form_data)


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
        self._expand_descriptions(["publisher", "society_institution", "platform"])

    def source2form(self):
        self.form = forms.ManEdApplicationReviewForm(data=xwalk.SuggestionFormXWalk.obj2form(self.source))
        self._set_choices()
        self._expand_descriptions(["publisher", "society_institution", "platform"])

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

        if self.source.application_status == "accepted":
            raise FormContextException("You cannot edit applications which have been accepted into DOAJ.")

        # if we are allowed to finalise, kick this up to the superclass
        super(ManEdApplicationReview, self).finalise()

        # FIXME: may want to factor this out of the suggestionformxwalk
        email_editor = xwalk.SuggestionFormXWalk.is_new_editor_group(self.form, self.source)
        email_associate = xwalk.SuggestionFormXWalk.is_new_editor(self.form, self.source)

        # Save the target
        self.target.save()

        # if this application is being accepted, then do the conversion to a journal
        if self.target.application_status == 'accepted':
            # this suggestion is just getting accepted
            j = self.target.make_journal()
            j.set_in_doaj(True)
            j.save()

            # record the url the journal is available at in the admin are and alert the user
            jurl = url_for("admin.journal_page", journal_id=j.id)
            self.add_alert('<a href="{url}" target="_blank">New journal created</a>.'.format(url=jurl))

            # create the user account for the owner and send the notification email
            owner = self._create_account_on_suggestion_approval(self.target, j)
            self._send_suggestion_approved_email(j.bibjson().title, owner.email)

        # if we need to email the editor and/or the associate, handle those here
        if email_editor:
            self._send_editor_group_email(self.target)
        if email_associate:
            self._send_editor_email(self.target)

    def render_template(self, **kwargs):
        if self.source is None:
            raise FormContextException("You cannot edit a not-existent application")

        return super(ManEdApplicationReview, self).render_template(
            lcc_jstree=json.dumps(lcc_jstree),
            subjectstr=self._subjects2str(self.source.bibjson().subjects()),
            **kwargs)

    def _set_choices(self):
        self.form.application_status.choices = choices.Choices.application_status("admin")
        editor = self.form.editor.data
        if editor is not None:
            self.form.editor.choices = [(editor, editor)]
        else:
            self.form.editor.choices = [("", "")]


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
        self._expand_descriptions(["publisher", "society_institution", "platform"])

    def source2form(self):
        self.form = forms.EditorApplicationReviewForm(data=xwalk.SuggestionFormXWalk.obj2form(self.source))
        self._set_choices()
        self._expand_descriptions(["publisher", "society_institution", "platform"])

    def pre_validate(self):
        self.form.editor_group.data = self.source.editor_group
        if "application_status" in self.renderer.disabled_fields:
            self.form.application_status.data = "accepted"

    def form2target(self):
        self.target = xwalk.SuggestionFormXWalk.form2obj(self.form)

    def patch_target(self):
        if self.source is None:
            raise FormContextException("You cannot patch a target from a non-existent source")

        self._carry_fixed_aspects()
        self._merge_notes_forward()
        self.target.set_owner(self.source.owner)
        self.target.set_editor_group(self.source.editor_group)

    def finalise(self):
        # FIXME: this first one, we ought to deal with outside the form context, but for the time being this
        # can be carried over from the old implementation
        if self.source is None:
            raise FormContextException("You cannot edit a not-existent application")

        if self.source.application_status == "accepted":
            raise FormContextException("You cannot edit applications which have been accepted into DOAJ.")

        # if we are allowed to finalise, kick this up to the superclass
        super(EditorApplicationReview, self).finalise()

        # FIXME: may want to factor this out of the suggestionformxwalk
        email_associate = xwalk.SuggestionFormXWalk.is_new_editor(self.form, self.source)

        # Save the target
        self.target.save()

        # if we need to email the associate, handle that here
        if email_associate:
            self._send_editor_email(self.target)

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

        if self.form.application_status.data == "accepted":
            self.form.application_status.choices = choices.Choices.application_status("accepted")
            self.renderer.set_disabled_fields(self.renderer.disabled_fields + ["application_status"])
        else:
            self.form.application_status.choices = choices.Choices.application_status()

        # get the editor group from the source because it isn't in the form
        egn = self.source.editor_group
        if egn is None:
            self.form.editor.choices = [("", "")]
        else:
            eg = models.EditorGroup.pull_by_key("name", egn)
            if eg is not None:
                editors = [eg.editor]
                editors += eg.associates
                editors = list(set(editors))
                self.form.editor.choices = [("", "Choose an editor")] + [(editor, editor) for editor in editors]
            else:
                self.form.editor.choices = [("", "")]



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
        self._expand_descriptions(["publisher", "society_institution", "platform"])

    def source2form(self):
        self.form = forms.AssEdApplicationReviewForm(data=xwalk.SuggestionFormXWalk.obj2form(self.source))
        self._set_choices()
        self._expand_descriptions(["publisher", "society_institution", "platform"])

    def pre_validate(self):
        if "application_status" in self.renderer.disabled_fields:
            self.form.application_status.data = "accepted"

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

    def finalise(self):
        # FIXME: this first one, we ought to deal with outside the form context, but for the time being this
        # can be carried over from the old implementation
        if self.source is None:
            raise FormContextException("You cannot edit a not-existent application")

        if self.source.application_status == "accepted":
            raise FormContextException("You cannot edit applications which have been accepted into DOAJ.")

        # if we are allowed to finalise, kick this up to the superclass
        super(AssEdApplicationReview, self).finalise()

        # Save the target
        self.target.save()

    def render_template(self, **kwargs):
        if self.source is None:
            raise FormContextException("You cannot edit a not-existent application")

        return super(AssEdApplicationReview, self).render_template(
            lcc_jstree=json.dumps(lcc_jstree),
            subjectstr=self._subjects2str(self.source.bibjson().subjects()),
            **kwargs)

    def _set_choices(self):
        if self.form.application_status.data == "accepted":
            self.form.application_status.choices = choices.Choices.application_status("accepted")
            self.renderer.set_disabled_fields(self.renderer.disabled_fields + ["application_status"])
        else:
            self.form.application_status.choices = choices.Choices.application_status()

class PublisherCsvReApplication(ApplicationContext):
    def make_renderer(self):
        # this form does not have a UI expression, so no renderer required
        pass

    def set_template(self):
        # this form does not have a UI expression, so no template required
        self.template = None

    def blank_form(self):
        # this uses the same form as the UI for the publisher reapplication, since the requirements
        # are identical
        self.form = forms.PublisherReApplicationForm()

    def data2form(self):
        self.form = forms.PublisherReApplicationForm(formdata=self.form_data)

    def source2form(self):
        self.form = forms.PublisherReApplicationForm(data=xwalk.SuggestionFormXWalk.obj2form(self.source))

    def pre_validate(self):
        if self.source is None:
            raise FormContextException("You cannot validate a form from a non-existent source")

        bj = self.source.bibjson()
        contacts = self.source.contacts()

        self.form.pissn.data = bj.get_one_identifier(bj.P_ISSN)
        self.form.eissn.data = bj.get_one_identifier(bj.E_ISSN)

        if len(contacts) == 0:
            return

        contact = contacts[0]
        self.form.contact_name.data = contact.get("name")
        self.form.contact_email.data = contact.get("email")
        self.form.confirm_contact_email.data = contact.get("email")

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

        # we carry this over for completeness, although it will be overwritten in the finalise() method
        self.target.set_application_status(self.source.application_status)

    def finalise(self):
        # FIXME: this first one, we ought to deal with outside the form context, but for the time being this
        # can be carried over from the old implementation
        if self.source is None:
            raise FormContextException("You cannot edit a not-existent application")

        # if we are allowed to finalise, kick this up to the superclass
        super(PublisherCsvReApplication, self).finalise()

        # set the status to updated
        self.target.set_application_status('submitted')

        # Save the target
        self.target.save()

    def render_template(self, **kwargs):
        # there is no template to render
        return ""


class PublisherReApplication(ApplicationContext):
    def make_renderer(self):
        self.renderer = render.PublisherReApplicationRenderer()
        self.renderer.set_disabled_fields(["pissn", "eissn", "contact_name", "contact_email", "confirm_contact_email"])

    def set_template(self):
        self.template = "formcontext/publisher_reapplication.html"

    def blank_form(self):
        self.form = forms.PublisherReApplicationForm()

    def data2form(self):
        self.form = forms.PublisherReApplicationForm(formdata=self.form_data)
        self._expand_descriptions(["publisher", "society_institution", "platform"])

    def source2form(self):
        self.form = forms.PublisherReApplicationForm(data=xwalk.SuggestionFormXWalk.obj2form(self.source))
        self._expand_descriptions(["publisher", "society_institution", "platform"])

    def pre_validate(self):
        if self.source is None:
            raise FormContextException("You cannot validate a form from a non-existent source")

        bj = self.source.bibjson()
        contacts = self.source.contacts()

        self.form.pissn.data = bj.get_one_identifier(bj.P_ISSN)
        self.form.eissn.data = bj.get_one_identifier(bj.E_ISSN)

        if len(contacts) == 0:
            return

        contact = contacts[0]
        self.form.contact_name.data = contact.get("name")
        self.form.contact_email.data = contact.get("email")
        self.form.confirm_contact_email.data = contact.get("email")

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

        # we carry this over for completeness, although it will be overwritten in the finalise() method
        self.target.set_application_status(self.source.application_status)

    def finalise(self):
        # FIXME: this first one, we ought to deal with outside the form context, but for the time being this
        # can be carried over from the old implementation
        if self.source is None:
            raise FormContextException("You cannot edit a not-existent application")

        # if we are allowed to finalise, kick this up to the superclass
        super(PublisherReApplication, self).finalise()

        # set the status to updated
        self.target.set_application_status('submitted')

        # Save the target
        self.target.save()

        # email the publisher to tell them we received their re-application
        self._send_received_email()

    def render_template(self, **kwargs):
        if self.source is None:
            raise FormContextException("You cannot edit a not-existent application")

        return super(PublisherReApplication, self).render_template(**kwargs)

    def _send_received_email(self):
        acc = models.Account.pull(self.target.owner)
        if acc is None:
            self.add_alert("Unable to locate account for specified owner")
            return

        journal_name = self.target.bibjson().title.encode('utf-8', 'replace')

        to = [acc.email]
        fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
        subject = app.config.get("SERVICE_NAME","") + " - re-application received"

        try:
            if app.config.get("ENABLE_PUBLISHER_EMAIL", False):
                app_email.send_mail(to=to,
                                    fro=fro,
                                    subject=subject,
                                    template_name="email/reapplication_received.txt",
                                    journal_name=journal_name.encode('utf-8', 'replace')
                )
                self.add_alert('Sent email to ' + acc.email + ' to tell them about their reapplication being received.')
            else:
                self.add_alert('Did not send email to ' + acc.email + ' to tell them about their reapplication being received, as publisher emails are disabled.')
        except Exception as e:
            magic = str(uuid.uuid1())
            self.add_alert('Hm, sending the reapplication received email didn\'t work. Please quote this magic number when reporting the issue: ' + magic + ' . Thank you!')
            app.logger.error(magic + "\n" + repr(e))
            raise e


class PublicApplication(FormContext):
    """
    Public Application Form Context.  This is also a sort of demonstrator as to how to implement
    one, so it will do unnecessary things like override methods that don't actually need to be overridden.

    This should be used in a context where an unauthenticated user is making a request to put a journal into the
    DOAJ.  It does not have any edit capacity (i.e. the form can only be submitted once), and it does not provide
    any form fields other than the essential journal bibliographic, application bibliographc and contact information
    for the suggester.  On submission, it will set the status to "pending" and the item will be available for review
    by the editors
    """

    def __init__(self, form_data=None, source=None):
        #  initialise the object through the superclass
        super(PublicApplication, self).__init__(form_data=form_data, source=source)

    ############################################################
    # PublicApplicationForm versions of FormContext lifecycle functions
    ############################################################

    def make_renderer(self):
        self.renderer = render.PublicApplicationRenderer()

    def set_template(self):
        self.template = "formcontext/public_application_form.html"

    def pre_validate(self):
        # no pre-validation requirements
        pass

    def blank_form(self):
        self.form = forms.PublicApplicationForm()

    def data2form(self):
        self.form = forms.PublicApplicationForm(formdata=self.form_data)

    def source2form(self):
        self.form = forms.PublicApplicationForm(data=xwalk.SuggestionFormXWalk.obj2form(self.source))

    def form2target(self):
        self.target = xwalk.SuggestionFormXWalk.form2obj(self.form)

    def patch_target(self):
        # no need to patch the target, there is no source for this kind of form, and no complexity
        # in how it is handled
        pass

    def finalise(self):
        super(PublicApplication, self).finalise()

        # set some administrative data
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.target.suggested_on = now
        self.target.set_application_status('pending')

        # Finally save the target
        self.target.save()

        self._send_received_email()

    def _send_received_email(self):
        suggester = self.target.suggester

        to = [suggester.get("email")]
        fro = app.config.get('SYSTEM_EMAIL_FROM', 'feedback@doaj.org')
        subject = app.config.get("SERVICE_NAME","") + " - your application to DOAJ has been received"

        app_email.send_mail(to=to,
                            fro=fro,
                            subject=subject,
                            template_name="email/suggestion_received.txt",
                            suggestion=self.target,
                            )

### Journal form contexts ###

class ManEdJournalReview(PrivateContext):
    """
    Managing Editor's Journal Review form.  Should be used in a context where the form warrants full
    admin privileges.  It will permit doing every.
    """
    def make_renderer(self):
        self.renderer = render.ManEdJournalReviewRenderer()

    def set_template(self):
        self.template = "formcontext/maned_journal_review.html"

    def render_template(self, **kwargs):
        if self.source is None:
            raise FormContextException("You cannot edit a not-existent journal")

        return super(PrivateContext, self).render_template(
            lcc_jstree=json.dumps(lcc_jstree),
            subjectstr=self._subjects2str(self.source.bibjson().subjects()),
            **kwargs)

    def blank_form(self):
        self.form = forms.ManEdApplicationReviewForm()
        self._set_choices()

    def data2form(self):
        self.form = forms.ManEdJournalReviewForm(formdata=self.form_data)
        self._set_choices()
        self._expand_descriptions(["publisher", "society_institution", "platform"])

    def source2form(self):
        self.form = forms.ManEdJournalReviewForm(data=xwalk.JournalFormXWalk.obj2form(self.source))
        self._set_choices()
        self._expand_descriptions(["publisher", "society_institution", "platform"])

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
        editor = self.form.editor.data
        if editor is not None:
            self.form.editor.choices = [(editor, editor)]
        else:
            self.form.editor.choices = [("", "")]

    def finalise(self):
        # FIXME: this first one, we ought to deal with outside the form context, but for the time being this
        # can be carried over from the old implementation

        if self.source is None:
            raise FormContextException("You cannot edit a not-existent journal")

        # if we are allowed to finalise, kick this up to the superclass
        super(PrivateContext, self).finalise()

        # Save the target
        self.target.save()

    def validate(self):
        # make use of the ability to disable validation, otherwise, let it run
        if self.form is not None:
            if self.form.make_all_fields_optional.data:
                return True

        return super(ManEdJournalReview, self).validate()


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

        return super(PrivateContext, self).render_template(
            lcc_jstree=json.dumps(lcc_jstree),
            subjectstr=self._subjects2str(self.source.bibjson().subjects()),
            **kwargs)

    def blank_form(self):
        self.form = forms.EditorJournalReviewForm()
        self._set_choices()

    def data2form(self):
        self.form = forms.EditorJournalReviewForm(formdata=self.form_data)
        self._set_choices()
        self._expand_descriptions(["publisher", "society_institution", "platform"])

    def source2form(self):
        self.form = forms.EditorJournalReviewForm(data=xwalk.JournalFormXWalk.obj2form(self.source))
        self._set_choices()
        self._expand_descriptions(["publisher", "society_institution", "platform"])

    def form2target(self):
        self.target = xwalk.JournalFormXWalk.form2obj(self.form)

    def patch_target(self):
        if self.source is None:
            raise FormContextException("You cannot patch a target from a non-existent source")

        self._carry_fixed_aspects()
        self.target.set_owner(self.source.owner)
        self.target.set_editor_group(self.source.editor_group)
        self._merge_notes_forward()

    def pre_validate(self):
        self.form.editor_group.data = self.source.editor_group

    def _set_choices(self):
        if self.source is None:
            raise FormContextException("You cannot set choices for a non-existent source")

        # get the editor group from the source because it isn't in the form
        egn = self.source.editor_group
        if egn is None:
            self.form.editor.choices = [("", "")]
        else:
            eg = models.EditorGroup.pull_by_key("name", egn)
            if eg is not None:
                editors = [eg.editor]
                editors += eg.associates
                editors = list(set(editors))
                self.form.editor.choices = [("", "Choose an editor")] + [(editor, editor) for editor in editors]
            else:
                self.form.editor.choices = [("", "")]

    def finalise(self):
        # FIXME: this first one, we ought to deal with outside the form context, but for the time being this
        # can be carried over from the old implementation

        if self.source is None:
            raise FormContextException("You cannot edit a not-existent journal")

        # if we are allowed to finalise, kick this up to the superclass
        super(PrivateContext, self).finalise()

        # Save the target
        self.target.save()


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
        self._expand_descriptions(["publisher", "society_institution", "platform"])

    def source2form(self):
        self.form = forms.AssEdJournalReviewForm(data=xwalk.JournalFormXWalk.obj2form(self.source))
        self._set_choices()
        self._expand_descriptions(["publisher", "society_institution", "platform"])

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

    def finalise(self):
        # FIXME: this first one, we ought to deal with outside the form context, but for the time being this
        # can be carried over from the old implementation
        if self.source is None:
            raise FormContextException("You cannot edit a not-existent journal")

        # if we are allowed to finalise, kick this up to the superclass
        super(AssEdJournalReview, self).finalise()

        # Save the target
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

