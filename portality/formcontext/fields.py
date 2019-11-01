from wtforms import Field, TextField, SelectField, SelectMultipleField, RadioField
from wtforms import widgets
import re

URL_REQUIRED_SCHEME_REGEX = re.compile(r'^[a-z]+://([^/:]+\.[a-z]{2,10}|([0-9]{1,3}\.){3}[0-9]{1,3})(:[0-9]+)?(\/.*)?$', re.IGNORECASE)


def set_select_field_default(kwargs):
    if 'default' not in kwargs:
        kwargs['default'] = ''


class DOAJSelectField(SelectField):
    def __init__(self, *args, **kwargs):
        set_select_field_default(kwargs)
        super(DOAJSelectField, self).__init__(*args, **kwargs)


class DOAJSelectMultipleField(SelectMultipleField):
    def __init__(self, *args, **kwargs):
        set_select_field_default(kwargs)
        super(DOAJSelectMultipleField, self).__init__(*args, **kwargs)
        self.type = 'SelectMultipleField'


class OptionalRadioField(RadioField):
    """Use this class if you want to have an optional radio button. I.e. if you use validators.Optional() on a radio button, use this class instead of wtforms.RadioButton."""
    # it's to do with what happens to the default choice for a RadioField - None
    # by default it will fail WTForms validation since WTForms will only accept
    # what we have defined as choices for the field. For radio buttons those
    # don't ever include None.
    def pre_validate(self, form):
        if self.data is None:
            return
        super(OptionalRadioField, self).pre_validate(form)

class TagListField(Field):
    widget = widgets.TextInput()

    def _value(self):
        if self.data:
            return u', '.join(self.data)
        else:
            return u''

    def get_list(self):
        return self.data

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = []
            for v in valuelist:
                self.data += [c for c in [x.strip() for x in v.split(",") if x]]
        else:
            self.data = []


class URLField(TextField):
    widget = widgets.TextInput()

    def process_formdata(self, valuelist):
        if valuelist is None or len(valuelist) == 0:
             self.data = self.data = u''
        else:
            val = valuelist[0]
            assumed_scheme = 'http://'

            if val and not val.startswith(assumed_scheme) and not URL_REQUIRED_SCHEME_REGEX.match(val):
                self.data = assumed_scheme + val
            else:
                if val == assumed_scheme:  # just to prevent http:// from showing up on its own in all the URL fields when you make a mistake elsewhere
                    self.data = u''
                else:
                    self.data = val


class DisabledTextField(TextField):

    def __call__(self, *args, **kwargs):
        kwargs.setdefault('disabled', True)
        return super(DisabledTextField, self).__call__(*args, **kwargs)


class PermissiveSelectField(DOAJSelectField):
    """ A SelectField with validation disabled, allowing us to change the choices in JS and validate later."""

    def iter_choices(self):
        for value, label in self.choices:
            yield (value, label, self.coerce(value) == self.data)

    def pre_validate(self, form):
        pass

