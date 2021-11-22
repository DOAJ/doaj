from wtforms import Field, SelectField, FormField, RadioField
from wtforms import widgets


class DOAJSelectField(SelectField):
    def __init__(self, *args, **kwargs):
        if 'default' not in kwargs:
            kwargs['default'] = ''
        super(DOAJSelectField, self).__init__(*args, **kwargs)


class TagListField(Field):
    widget = widgets.TextInput()

    def _value(self):
        if self.data:
            return ', '.join(self.data)
        else:
            return ''

    def get_list(self):
        return self.data

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = []
            for v in valuelist:
                self.data += [c for c in [x.strip() for x in v.split(",") if x]]
        else:
            self.data = []


class NestedFormField(FormField):
    def validate(self, form, extra_validators=tuple()):
        self.form.meta.parent_form = form
        return super().validate(form, extra_validators)


class UnconstrainedRadioField(RadioField):
    def pre_validate(self, form):
        return

    def process_data(self, value):
        if value:
            super(UnconstrainedRadioField, self).process_data(value)
        else:
            self.data = None