from flask import render_template, url_for
import json
from datetime import datetime

from portality.formcontext import forms, xwalk, render, choices
from portality.lcc import lcc_jstree
from portality import models, journal, app_email
from portality.core import app
from portality.account import create_account_on_suggestion_approval, send_suggestion_approved_email

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


class ApplicationAdmin(FormContext):
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
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        # copy over any important fields from the previous version of the object
        created_date = self.source.created_date if self.source.created_date else now
        self.target.set_created(created_date)
        self.target.suggested_on = self.source.suggested_on
        self.target.data['id'] = self.source.data['id']

    def _send_editor_group_email(self, suggestion):
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

    def _send_editor_email(self, suggestion):
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

class JournalFormFactory(object):
    @classmethod
    def get_form_context(cls, role=None, source=None, form_data=None):
        if role is None:
            return PublicApplication(source=source, form_data=form_data)
        elif role == "admin":
            return ManEdApplicationReview(source=source, form_data=form_data)
        elif role == "editor":
            return EditorApplicationReview(source=source, form_data=form_data)

class ManEdApplicationReview(ApplicationAdmin):
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
        self._carry_fixed_aspects()

        # NOTE: this means you can't unset an owner once it has been set.  But you can change it.
        if (self.target.owner is None or self.target.owner == "") and (self.source.owner is not None):
            self.target.set_owner(self.source.owner)

    def finalise(self):
        # FIXME: this first one, we ought to deal with outside the form context, but for the time being this
        # can be carried over from the old implementation
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
            j = journal.suggestion2journal(self.target)  # FIXME: rationalise with journal xwalk/module
            j.set_in_doaj(True)
            j.save()

            # record the url the journal is available at in the admin are and alert the user
            jurl = url_for("admin.journal_page", journal_id=j.id)
            self.add_alert('<a href="{url}" target="_blank">New journal created</a>.'.format(url=jurl))

            # create the user account for the owner and send the notification email
            owner = create_account_on_suggestion_approval(self.target, j)
            send_suggestion_approved_email(j.bibjson().title, owner.email)

        # if we need to email the editor and/or the associate, handle those here
        if email_editor:
            self._send_editor_group_email(self.target)
        if email_associate:
            self._send_editor_email(self.target)

    def _set_choices(self):
        self.form.application_status.choices = choices.Choices.application_status("admin")
        editor = self.form.editor.data
        if editor is not None:
            self.form.editor.choices = [(editor, editor)]
        else:
            self.form.editor.choices = [("", "")]

    def render_template(self, **kwargs):
        return super(ManEdApplicationReview, self).render_template(lcc_jstree=json.dumps(lcc_jstree), **kwargs)

class EditorApplicationReview(ApplicationAdmin):
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
        self._carry_fixed_aspects()
        self.target.set_owner(self.source.owner)
        self.target.set_editor_group(self.source.editor_group)

    def finalise(self):
        # FIXME: this first one, we ought to deal with outside the form context, but for the time being this
        # can be carried over from the old implementation
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
        return super(EditorApplicationReview, self).render_template(lcc_jstree=json.dumps(lcc_jstree), **kwargs)


    def _set_choices(self):
        if self.form.application_status.data == "accepted":
            self.form.application_status.choices = choices.Choices.application_status("accepted")
            self.renderer.set_disabled_fields(self.renderer.disabled_fields + ["application_status"])
        else:
            self.form.application_status.choices = choices.Choices.application_status()

        eg = models.EditorGroup.pull_by_key("name", self.source.editor_group)
        if eg is not None:
            editors = [eg.editor]
            editors += eg.associates
            editors = list(set(editors))
            self.form.editor.choices = [("", "Choose an editor")] + [(editor, editor) for editor in editors]
        else:
            self.form.editor.choices = [("", "")]

class PublicApplication(FormContext):
    """
    Public Application Form Context.  This is also a sort of demonstrator as to how to implement
    one, so it will do unnecessary things like override methods that don't actually need to be overridden
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

