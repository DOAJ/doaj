import re
from flask_login import current_user
from wtforms import validators
from wtforms.compat import string_types
from typing import List

from portality.core import app
from portality.lib import dates
from portality.lib.dates import FMT_DATE_STD
from portality.models import Journal, EditorGroup, Account

from datetime import datetime
from portality import regex


class MultiFieldValidator(object):
    """ A validator that accesses the value of an additional field """

    def __init__(self, other_field, *args, **kwargs):
        self.other_field_name = other_field
        super(MultiFieldValidator, self).__init__(*args, **kwargs)

    @staticmethod
    def get_other_field(field_name, form):
        other_field = form._fields.get(field_name)
        if not other_field:
            if hasattr(form.meta, "parent_form"):
                other_field = MultiFieldValidator.get_other_field(field_name, form.meta.parent_form)
            else:
                raise Exception('No field named "{0}" in form (or its parent containers)'.format(field_name))
        return other_field


class DataOptional(object):
    """
    Allows empty input and stops the validation chain from continuing.

    If input is empty, also removes prior errors (such as processing errors)
    from the field.

    This is a near-clone of the WTForms standard Optional class, except that
    it checks the .data parameter not the .raw_data parameter, which allows us
    to check coerced fields correctly.

    ~~DataOptional:FormValidator~~

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


class OptionalIf(DataOptional, MultiFieldValidator):
    # A validator which makes a field optional if another field is set
    # and has a truthy value.
    # ~~OptionalIf:FormValidator~~

    def __init__(self, other_field_name, message=None, optvals=None, *args, **kwargs):
        self.other_field_name = other_field_name
        if not message:
            message = "This field is required in the current circumstances"
        self.message = message
        self.optvals = optvals if optvals is not None else []
        super(OptionalIf, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = self.get_other_field(self.other_field_name, form)

        # if no values (for other_field) which make this field optional
        # are specified...
        if not self.optvals:
            # ... just make this field optional if the other is truthy
            if bool(other_field.data):
                super(OptionalIf, self).__call__(form, field)
            else:
                # otherwise it is required
                dr = validators.DataRequired(self.message)
                dr(form, field)
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


class HTTPURL(validators.Regexp):
    """
    Simple regexp based url validation. Much like the email validator, you
    probably want to validate the url later by other means if the url must
    resolve.

    ~~HTTPURL:FormValidator~~

    :param require_tld:
        If true, then the domain-name portion of the URL must contain a .tld
        suffix.  Set this to false if you want to allow domains like
        `localhost`.
    :param message:
        Error message to raise in case of a validation error.
    """
    def __init__(self, message=None):
        super(HTTPURL, self).__init__(regex.HTTP_URL, re.IGNORECASE, message)

    def __call__(self, form, field, message=None):
        message = self.message
        if message is None:
            message = field.gettext('Invalid URL.')

        if field.data:
            super(HTTPURL, self).__call__(form, field, message)


class MaxLen(object):
    """
    Maximum length validator. Works on anything which supports len(thing).

    Use {max_len} in your custom message to insert the maximum length you've
    specified into the message.

    ~~MaxLen:FormValidator~~
    """

    def __init__(self, max_len, message='Maximum {max_len}.', *args, **kwargs):
        self.max_len = max_len
        self.message = message

    def __call__(self, form, field):
        if len(field.data) > self.max_len:
            raise validators.ValidationError(self.message.format(max_len=self.max_len))


class RequiredIfRole(validators.DataRequired):
    """
    Makes a field required, if the user has the specified role

    ~~RequiredIfRole:FormValidator~~
    """

    def __init__(self, role, *args, **kwargs):
        self.role = role
        super(RequiredIfRole, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        if current_user.has_role(self.role):
            super(RequiredIfRole, self).__call__(form, field)


class RegexpOnTagList(object):
    """
    Validates the field against a user provided regexp.

    ~~RegexpOnTagList:FormValidator~~

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


class ThisOrThat(MultiFieldValidator):
    """
    ~~ThisOrThat:FormValidator~~
    """
    def __init__(self, other_field_name, message=None, *args, **kwargs):
        self.message = message
        super(ThisOrThat, self).__init__(other_field_name, *args, **kwargs)

    def __call__(self, form, field):
        other_field = self.get_other_field(self.other_field_name, form)
        this = bool(field.data)
        that = bool(other_field.data)
        if not this and not that:
            if not self.message:
                self.message = "Either this field or " + other_field.label.text + " is required"
            raise validators.ValidationError(self.message)


class ReservedUsernames(object):
    """
    A username validator. When applied to fields containing usernames it prevents
    their use if they are reserved.

    ~~ReservedUsernames:FormValidator~~
    """
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


class OwnerExists(object):
    """
    A username validator. When applied to fields containing usernames it ensures that the username
    exists

    ~~OwnerExists:FormValidator~~
    """
    def __init__(self, message='The "{reserved}" user does not exist. Please choose an existing username, or create a new account first.', *args, **kwargs):
        self.message = message

    def __call__(self, form, field):
        return self.__validate(field.data)

    def __validate(self, username):
        if not isinstance(username, str):
            raise validators.ValidationError('Invalid username (not a string) passed to OwnerExists validator.')

        if username == "":
            return

        acc = Account.pull(username)
        if not acc:
            raise validators.ValidationError(self.message.format(reserved=username))

    @classmethod
    def validate(cls, username):
        return cls().__validate(username)


class ISSNInPublicDOAJ(object):
    """
    ~~ISSNInPublicDOAJ:FormValidator~~
    """
    def __init__(self, message=None):
        if not message:
            message = "This ISSN already appears in the public DOAJ database"
        self.message = message

    def __call__(self, form, field):
        if field.data is not None:
            existing = Journal.find_by_issn(field.data, in_doaj=True, max=1)
            if len(existing) > 0:
                raise validators.ValidationError(self.message)


class JournalURLInPublicDOAJ(object):
    """
    ~~JournalURLInPublicDOAJ:FormValidator~~
    """
    def __init__(self, message=None):
        if not message:
            message = "This Journal URL already appears in the public DOAJ database"
        self.message = message

    def __call__(self, form, field):
        if field.data is not None:
            existing = Journal.find_by_journal_url(field.data, in_doaj=True, max=1)
            if len(existing) > 0:
                raise validators.ValidationError(self.message)


class StopWords(object):
    """
    ~~StopWords:FormValidator~~
    """
    def __init__(self, stopwords, message=None):
        self.stopwords = stopwords
        if not message:
            message = "You may not enter '{stop_word}' in this field"
        self.message = message

    def __call__(self, form, field):
        for v in field.data:
            if v.strip() in self.stopwords:
                raise validators.StopValidation(self.message.format(stop_word=v))


class DifferentTo(MultiFieldValidator):
    """
    ~~DifferentTo:FormValidator~~
    """
    def __init__(self, other_field_name, ignore_empty=True, message=None):
        super(DifferentTo, self).__init__(other_field_name)
        self.ignore_empty = ignore_empty
        if not message:
            message = "This field must contain a different value to the field '{x}'".format(x=self.other_field_name)
        self.message = message

    def __call__(self, form, field):
        other_field = self.get_other_field(self.other_field_name, form)

        if other_field.data == field.data:
            if self.ignore_empty and (not other_field.data or not field.data):
                return
            raise validators.ValidationError(self.message)


class RequiredIfOtherValue(MultiFieldValidator):
    """
    Makes a field required, if the user has selected a specific value in another field

    ~~RequiredIfOtherValue:FormValidator~~
    """

    def __init__(self, other_field_name, other_value, message=None, *args, **kwargs):
        self.other_value = other_value
        self.message = message if message is not None else "This field is required when {x} is {y}".format(x=other_field_name, y=other_value)
        super(RequiredIfOtherValue, self).__init__(other_field_name, *args, **kwargs)

    def __call__(self, form, field):
        # attempt to get the other field - if it doesn't exist, just take this as valid
        try:
            other_field = self.get_other_field(self.other_field_name, form)
        except:
            return

        if isinstance(self.other_value, list):
            self._match_list(form, field, other_field)
        else:
            self._match_single(form, field, other_field)

    def _match_single(self, form, field, other_field):
        if isinstance(other_field.data, list):
            match = self.other_value in other_field.data
        else:
            match = other_field.data == self.other_value
        if match:
            dr = validators.DataRequired(self.message)
            dr(form, field)
        else:
            if not field.data or (isinstance(field.data, str) and not field.data.strip()):
                raise validators.StopValidation()

    def _match_list(self, form, field, other_field):
        if isinstance(other_field.data, list):
            match = len(list(set(self.other_value) & set(other_field.data))) > 0
        else:
            match = other_field.data in self.other_value
        if match:
            dr = validators.DataRequired(self.message)
            dr(form, field)
        else:
            if not field.data or len(field.data) == 0:
                raise validators.StopValidation()


class OnlyIf(MultiFieldValidator):
    """
    Field only validates if other fields have specific values (or are truthy)
    ~~OnlyIf:FormValidator~~
    """
    def __init__(self, other_fields: List[dict], ignore_empty=True, message=None, *args, **kwargs):
        self.other_fields = other_fields
        self.ignore_empty = ignore_empty
        if not message:
            fieldnames = [n['field'] for n in self.other_fields]
            message = "This field can only be selected with valid values in other fields: '{x}'".format(x=fieldnames)
        self.message = message
        super(OnlyIf, self).__init__(None, *args, **kwargs)

    def __call__(self, form, field):
        if field.data is None or field.data is False or isinstance(field.data, str) and not field.data.strip():
            return

        others = self.get_other_fields(form)

        for o_f in self.other_fields:
            other = others[o_f["field"]]
            if self.ignore_empty and (not other.data or not field.data):
                continue
            if o_f.get("or") is not None:
                # succeed if the value is in the list
                if other.data in o_f["or"]:
                    continue
            if o_f.get('not') is not None:
                # Succeed if the value doesn't equal the one specified
                if other.data != o_f['not']:
                    continue
            if o_f.get('value') is not None:
                if other.data == o_f['value']:
                    # Succeed if the other field has the specified value
                    continue
            if o_f.get('value') is None:
                # No target value supplied - succeed if the other field is truthy
                if other.data:
                    continue
            raise validators.ValidationError(self.message)

    def get_other_fields(self, form):
        # return the actual fields matching the names in self.other_fields
        others = {f["field"]: self.get_other_field(f["field"], form) for f in self.other_fields}
        return others


class NotIf(OnlyIf):
    """
    Field only validates if other fields DO NOT have specific values (or are truthy)
    ~~NotIf:FormValidator~~
    """

    def __call__(self, form, field):
        others = self.get_other_fields(form)

        for o_f in self.other_fields:
            other = others[o_f["field"]]
            if self.ignore_empty and (not other.data or not field.data):
                continue
            if o_f.get('value') is None:
                # Fail if the other field is truthy
                if other.data:
                    validators.ValidationError(self.message)
            elif other.data == o_f['value']:
                # Fail if the other field has the specified value
                validators.ValidationError(self.message)


class NoScriptTag(object):
    """
    Checks that a field does not contain a script html tag
    ~~NoScriptTag:FormValidator~~
    """

    def __init__(self, message=None):
        if not message:
            message = "Value cannot contain script tag"
        self.message = message

    def __call__(self, form, field):
        if field.data is not None and "<script>" in field.data:
            raise validators.ValidationError(self.message)


class GroupMember(MultiFieldValidator):
    """
    Validation passes when a field's value is a member of the specified group
    ~~GroupMember:FormValidator~~
    """
    # Fixme: should / can this be generalised to any group vs specific to editor groups?

    def __init__(self, group_field_name, *args, **kwargs):
        super(GroupMember, self).__init__(group_field_name, *args, **kwargs)

    def __call__(self, form, field):
        group_field = self.get_other_field(self.other_field_name, form)

        """ Validate the choice of editor, which could be out of sync with the group in exceptional circumstances """
        # lifted from from formcontext
        editor = field.data
        if editor is not None and editor != "":
            editor_group_name = group_field.data
            if editor_group_name is not None and editor_group_name != "":
                eg = EditorGroup.pull_by_key("name", editor_group_name)
                if eg is not None:
                    if eg.is_member(editor):
                        return  # success - an editor group was found and our editor was in it
                raise validators.ValidationError("Editor '{0}' not found in editor group '{1}'".format(editor, editor_group_name))
            else:
                raise validators.ValidationError("An editor has been assigned without an editor group")


class RequiredValue(object):
    """
    Checks that a field contains a required value
    ~~RequiredValue:FormValidator~~
    """
    def __init__(self, value, message=None):
        self.value = value
        if not message:
            message = "You must enter {value}"
        self.message = message

    def __call__(self, form, field):
        if field.data != self.value:
            raise validators.ValidationError(self.message.format(value=self.value))


class BigEndDate(object):
    """
    ~~BigEndDate:FormValidator~~
    """
    def __init__(self, value, message=None):
        self.value = value
        self.message = message or "Date must be a big-end formatted date (e.g. 2020-11-23)"

    def __call__(self, form, field):
        if not field.data:
            return
        try:
            datetime.strptime(field.data, FMT_DATE_STD)
        except Exception:
            raise validators.ValidationError(self.message)

class Year(object):
    def __init__(self, value, message=None):
        self.value = value
        self.message = message or "Date must be a year in 4 digit format (eg. 1987)"

    def __call__(self, form, field):
        if not field.data:
            return
        return app.config.get('MINIMAL_OA_START_DATE', 1900) <= field.data <= dates.now().year


class CustomRequired(object):
    """
    ~~CustomRequired:FormValidator~~
    """
    field_flags = ('required', )

    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        if field.data is None or isinstance(field.data, str) and not field.data.strip() or isinstance(field.data, list) and len(field.data) == 0:
            if self.message is None:
                message = field.gettext('This field is required.')
            else:
                message = self.message

            field.errors[:] = []
            raise validators.StopValidation(message)


class EmailAvailable(object):
    """
    ~~EmailAvailable:FormValidator~~
    """
    def __init__(self, message=None):
        if not message:
            message = "Email address is already in use"
        self.message = message

    def __call__(self, form, field):
        if field.data is not None:
            existing = Account.email_in_use(field.data)
            if existing is True:
                raise validators.ValidationError(self.message)


class IdAvailable(object):
    """
    ~~IdAvailable:FormValidator~~
    """
    def __init__(self, message=None):
        if not message:
            message = "Account ID already in use"
        self.message = message

    def __call__(self, form, field):
        if field.data is not None:
            existing = Account.pull(field.data)
            if existing is not None:
                raise validators.ValidationError(self.message)


class IgnoreUnchanged(object):
    """
    Disables validation when the input is unchanged and stops the validation chain from continuing.

    If input is the same as before, also removes prior errors (such as processing errors)
    from the field.

    ~~IgnoreUnchanged:FormValidator~~

    """
    field_flags = ('optional', )

    def __call__(self, form, field):
        if field.data and field.object_data and field.data == field.object_data:
            field.errors[:] = []
            raise validators.StopValidation()
