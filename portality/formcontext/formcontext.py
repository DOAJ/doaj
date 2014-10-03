from portality.formcontext import forms, xwalk, render
from flask import render_template

class FormContext(object):
    def __init__(self, form_data=None, source=None):
        # initialise our core properties
        self._source = source
        self._target = None
        self._form_data = form_data
        self._form = None
        self._renderer = None
        self._template = None

        # now create our form instance, with the form_data (if there is any)
        if form_data is not None:
            self.data2form()

        # if there isn't any form data, then we should create the form properties from source instead
        elif source is not None:
            self.source2form()

        # if there is no source, then a blank form object
        else:
            self.blank_form()

        # initialise the renderer (falling back to a default if necessary)
        self.make_renderer()
        if self.renderer is None:
            self.renderer = render.Renderer()

        # specify the jinja template that will wrap the renderer
        self.set_template()

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

    def is_disabled(self, form_field):
        """Is the given field to be displayed as a disabled form field?"""
        return False

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



class JournalFormFactory(object):
    @classmethod
    def get_form_context(cls, role=None, source=None, form_data=None):
        if role is None:
            return PublicApplication(source=source, form_data=form_data)

class PublicApplication(FormContext):
    """
    Public Application Form Context.  This is also a sort of demonstrator as to how to implement
    one, so it will do unnecessary things like override methods that don't actually need to be overridden
    """

    def __init__(self, form_data=None, source=None, renderer=None):
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
        self.form = forms.PublicApplicationForm(obj=xwalk.SuggestionFormXWalk.obj2form(self.source))

    def form2target(self):
        self.target = xwalk.SuggestionFormXWalk.form2obj(self.form)

    def patch_target(self):
        # no need to patch the target, there is no source for this kind of form, and no complexity
        # in how it is handled
        pass

    def finalise(self):
        super(PublicApplication, self).finalise()

        # What happens next?  We probably need to save the target
        self.target.save()

    def is_disabled(self, form_field):
        # There are no disabled fields
        return False

