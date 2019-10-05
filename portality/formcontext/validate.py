from flask_login import current_user
from wtforms import validators
import re
from wtforms.compat import string_types

from portality.formcontext.choices import Choices
from portality.core import app

class DataOptional(object):
    """
    Allows empty input and stops the validation chain from continuing.

    If input is empty, also removes prior errors (such as processing errors)
    from the field.

    This is a near-clone of the WTForms standard Optional class, except that
    it checks the .data parameter not the .raw_data parameter, which allows us
    to check coerced fields correctly.

    :param strip_whitespace:
        If True (the default) also stop the validation chain on input which
        consists of only whitespace.
    """
    field_flags = ('optional', )

    def __init__(self, strip_whitespace=True):
        if strip_whitespace:
            self.string_check = lambda s: s.strip()
        else:
            self.string_check = lambda s: s

    def __call__(self, form, field):
        if not field.data or isinstance(field.data, string_types) and not self.string_check(field.data):
            field.errors[:] = []
            raise validators.StopValidation()

class OptionalIf(DataOptional):
    # A validator which makes a field optional if # another field is set
    # and has a truthy value.

    # Additionally, a list of values (optvals) can be specified - if any
    # of those values are present in the other field, this field becomes
    # optional. The other field having a truthy value is then no longer
    # sufficient.
    field_flags = ('display_required_star', )

    def __init__(self, other_field_name, optvals=None, *args, **kwargs):
        self.other_field_name = other_field_name
        self.optvals = optvals if optvals is not None else []
        super(OptionalIf, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = self.get_other_field(form)

        # if no values (for other_field) which make this field optional
        # are specified...
        if not self.optvals:
            # ... just make this field optional if the other is truthy
            if bool(other_field.data):
                super(OptionalIf, self).__call__(form, field)
        else:
            # if such values are specified, check for them
            no_optval_matched = True
            for v in self.optvals:
                if isinstance(other_field.data, list):
                    if v in other_field.data and len(other_field.data) == 1:
                        # must be the only option submitted - OK for
                        # radios and for checkboxes where a single
                        # checkbox, but no more, is required to make the
                        # field optional
                        no_optval_matched = False
                        self.__make_optional(form, field)
                        break
                if other_field.data == v:
                    no_optval_matched = False
                    self.__make_optional(form, field)
                    break

            if no_optval_matched:
                if not field.data:
                    raise validators.StopValidation('This field is required')

    def __make_optional(self, form, field):
        super(OptionalIf, self).__call__(form, field)
        raise validators.StopValidation()

    def get_other_field(self, form):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise Exception('no field named "%s" in form' % self.other_field_name)
        return other_field


class ExtraFieldRequiredIf(OptionalIf):
    '''Another field is required if this field has a certain value, but must be empty for all other values of this field.'''
    # A radio button has a related text field - we've got to:
    # a/ require a value in the text input if the related radio
    # button is checked.
    # b/ raise an error if there is text present but the related radio
    # button is not checked (people are far less likely to type text in
    # by accident compared to forgetting to click on a button, so we
    # cannot just ignore the text they've typed in).

    # All of this holds for a checkbox with a related text field too.

    def __init__(self, extra_field_name, reqval,
            message_empty='You have selected "{reqval}" but have not provided any details.',
            message_full='You have not selected "{reqval}" but have provided further details.',
            *args, **kwargs):
        self.extra_field_name = extra_field_name
        self.reqval = reqval
        self.message_empty = message_empty
        self.message_full = message_full
        super(ExtraFieldRequiredIf, self).__init__(extra_field_name, *args, **kwargs)

    def __call__(self, form, field):
        extra_field = self.get_extra_field(form)

        # case A - this field is checked, but there's no data in
        # the extra field
        if self.reqval in field.data: # works both if this field is a list (checkbox fields) and a string (radio or other fields)
            if not extra_field.data:
                raise validators.ValidationError(self.message_empty.format(reqval=self.reqval))

        # case B - the this field is not checked, but there is data in
        # the extra field
        if self.reqval not in field.data: # works both if this field is a list (checkbox fields) and a string (radio or other fields)
            if extra_field.data:
                raise validators.ValidationError(self.message_full.format(reqval=self.reqval))

    def get_extra_field(self, form):
        '''Alias get_other_field from the superclass to make its purpose clearer for this class.'''
        return self.get_other_field(form)


class ExclusiveCheckbox(object):
    '''If a checkbox is checked, do not allow any other checkboxes to be checked.'''
    # Using checkboxes as radio buttons is a Bad Idea (TM). Do not do it,
    # except where it will simplify a 50-field form, k?

    def __init__(self, exclusive_checkbox_value=Choices.NONE, message='When you have selected "{exclusive_checkbox_value}" you are not allowed to tick any other checkboxes.', *args, **kwargs):
        self.exclusive_checkbox_value = exclusive_checkbox_value
        self.message = message

    def __call__(self, form, field):
        detected_exclusive = False
        detected_others = False
        for val in field.data:
            if val == self.exclusive_checkbox_value:
                detected_exclusive = True
            else:
                if val:
                    detected_others = True

        # if only one of them is true, it doesn't matter
        # if both are false, no checkboxes have been checked - use a
        # validators.Required() on the checkboxes field for that
        # which leaves the case where both are True - and that is what
        # this validator is all about

        if detected_exclusive and detected_others:
            raise validators.ValidationError(self.message
                    .format(exclusive_checkbox_value=self.exclusive_checkbox_value)
            )
            # it won't insert the checkbox value anywhere if
            # {exclusive_checkbox_value} is not present in the message
            # passed to the constructor

class URLOptionalScheme(validators.Regexp):
    # copied from (around) https://github.com/wtforms/wtforms/blob/master/wtforms/validators.py#L375
    """
    Simple regexp based url validation. Much like the email validator, you
    probably want to validate the url later by other means if the url must
    resolve.

    :param require_tld:
        If true, then the domain-name portion of the URL must contain a .tld
        suffix.  Set this to false if you want to allow domains like
        `localhost`.
    :param message:
        Error message to raise in case of a validation error.
    """
    def __init__(self, require_tld=True, message=None):
        tld_part = (require_tld and r'\.[a-z]{2,10}' or '')
        # the original regex - the URL scheme is not optional
        #regex = r'^[a-z]+://([^/:]+s|([0-9]{1,3}\.){3}[0-9]{1,3})(:[0-9]+)?(\/.*)?$' % tld_part
        regex = r'^([a-z]+://){0,1}?([^/:]+%s|([0-9]{1,3}\.){3}[0-9]{1,3})(:[0-9]+)?(\/.*)?$' % tld_part
        super(URLOptionalScheme, self).__init__(regex, re.IGNORECASE, message)

    def __call__(self, form, field, message=None):
        message = self.message
        if message is None:
            message = field.gettext('Invalid URL.')

        super(URLOptionalScheme, self).__call__(form, field, message)


class MaxLen(object):
    '''
    Maximum length validator. Works on anything which supports len(thing).

    Use {max_len} in your custom message to insert the maximum length you've
    specified into the message.
    '''

    def __init__(self, max_len, message='Maximum {max_len}.', *args, **kwargs):
        self.max_len = max_len
        self.message = message

    def __call__(self, form, field):
        if len(field.data) > self.max_len:
            raise validators.ValidationError(self.message.format(max_len=self.max_len))

class RequiredIfRole(validators.Required):
    '''
    Makes a field required, if the user has the specified role
    '''

    def __init__(self, role, *args, **kwargs):
        self.role = role
        super(RequiredIfRole, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        if current_user.has_role(self.role):
            super(RequiredIfRole, self).__call__(form, field)

class RegexpOnTagList(object):
    """
    Validates the field against a user provided regexp.

    :param regex:
        The regular expression string to use. Can also be a compiled regular
        expression pattern.
    :param flags:
        The regexp flags to use, for example re.IGNORECASE. Ignored if
        `regex` is not a string.
    :param message:
        Error message to raise in case of a validation error.
    """
    def __init__(self, regex, flags=0, message=None):
        if isinstance(regex, string_types):
            regex = re.compile(regex, flags)
        self.regex = regex
        self.message = message

    def __call__(self, form, field, message=None):
        for entry in field.data:
            match = self.regex.match(entry or '')
            if not match:
                if message is None:
                    if self.message is None:
                        message = field.gettext('Invalid input.')
                    else:
                        message = self.message

                raise validators.ValidationError(message)

class ThisOrThat(object):
    def __init__(self, other_field_name, *args, **kwargs):
        self.other_field_name = other_field_name

    def __call__(self, form, field):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise Exception('no field named "%s" in form' % self.other_field_name)
        this = bool(field.data)
        that = bool(other_field.data)
        if not this and not that:
            raise validators.ValidationError("Either this field or " + other_field.label.text + " is required")


class ReservedUsernames(object):
    '''
    A username validator. When applied to fields containing usernames it prevents
    their use if they are reserved.
    '''
    def __init__(self, message='The "{reserved}" user is reserved. Please choose a different username.', *args, **kwargs):
        self.message = message

    def __call__(self, form, field):
        return self.__validate(field.data)

    def __validate(self, username):
        if not isinstance(username, str):
            raise validators.ValidationError('Invalid username (not a string) passed to ReservedUsernames validator.')

        if username.lower() in [u.lower() for u in app.config.get('RESERVED_USERNAMES', [])]:
            raise validators.ValidationError(self.message.format(reserved=username))

    @classmethod
    def validate(cls, username):
        return cls().__validate(username)
