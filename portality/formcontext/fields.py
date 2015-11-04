from wtforms import Field, TextField, SelectField
from wtforms import widgets
import re

URL_REQUIRED_SCHEME_REGEX = re.compile(r'^[a-z]+://([^/:]+\.[a-z]{2,10}|([0-9]{1,3}\.){3}[0-9]{1,3})(:[0-9]+)?(\/.*)?$', re.IGNORECASE)


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
            self.data = [clean_x for clean_x in [x.strip() for x in valuelist[0].split(',')] if clean_x]
        else:
            self.data = []


class URLField(TextField):
    widget = widgets.TextInput()

    def process_formdata(self, valuelist):
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


class PermissiveSelectField(SelectField):
    """ A SelectField with validation disabled, allowing us to change the choices in JS and validate later."""

    def iter_choices(self):
        for value, label in self.choices:
            yield (value, label, self.coerce(value) == self.data)

    def pre_validate(self, form):
        pass

