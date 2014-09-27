from portality.formcontext import forms
from portality.formcontext import xwalk

class FormContext(object):
    def __init__(self, form_data=None, source=None):
        # initialise our core properties
        self._source = source
        self._target = None
        self._form_data = form_data
        self._form = None

        # now create our form instance, with the form_data (if there is any)
        if form_data is not None:
            self.data2form()

        # if there isn't any form data, then we should create the form properties from source instead
        elif source is not None:
            self.source2form()

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

    ############################################################
    # Lifecycle functions that subclasses should implement
    ############################################################

    def is_disabled(self, form_field):
        """Is the given field to be displayed as a disabled form field?"""
        return False

    def pre_validate(self):
        """
        This will be run before validation against the form is run.
        Use it to patch the form with any relevant data, such as fields which were disabled
        """
        pass

    def data2form(self):
        """
        Convert the form_data into an instance of the form in this context, and write to self.form
        """
        pass

    def source2form(self):
        """
        Convert the source object into an instance of the form in this context, and write to self.form
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
        self.patch_target()

    ############################################################
    # Functions which can be called directly, but may be overridden if desired
    ############################################################

    def validate(self):
        self.pre_validate()
        f = self.form
        if f is not None:
            return f.validate()
        return False

    ############################################################
    # Render functions to be overridden
    ############################################################

    def render_form(self):
        pass

    def render_fields(self, field_list):
        pass

    def render_field(self, field):
        pass


class ApplicationFormFactory(object):
    @classmethod
    def get_form_context(cls, role=None, source=None, form_data=None):
        if role is None:
            return PublicApplicationForm(source=source, form_data=form_data)


class PublicApplicationForm(FormContext):
    """
    Public Application Form Context.  This is also a sort of demonstrator as to how to implement
    one, so it will do unnecessary things like override methods that don't actually need to be overridden
    """

    def __init__(self, form_data=None, source=None):
        #  initialise the object through the superclass
        super(PublicApplicationForm, self).__init__(form_data=form_data, source=source)

    ############################################################
    # PublicApplicationForm versions of FormContext lifecycle functions
    ############################################################

    def is_disabled(self, form_field):
        # There are no disabled fields
        return False

    def pre_validate(self):
        # no pre-validation requirements
        pass

    def data2form(self):
        self.form = forms.JournalInformationForm(self.form_data)

    def source2form(self):
        self.form = forms.JournalInformationForm(xwalk.SuggestionFormXWalk.obj2form(self.source))

    def form2target(self):
        self.target = xwalk.SuggestionFormXWalk.form2obj(self.form)

    def patch_target(self):
        # no need to patch the target, there is no source for this kind of form, and no complexity
        # in how it is handled
        pass

    def finalise(self):
        # we can call patch_target, though it won't have any effect.
        self.patch_target()

        # What happens next?  We probably need to save the target
        self.target.save()

