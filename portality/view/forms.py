'''
A forms system

Build a form template, build a handler for its submission, receive data from end users
'''
import json
import sys
import re
from datetime import datetime

from flask import Blueprint, request, abort, make_response, render_template, flash, redirect, url_for
from flask.ext.login import current_user

from wtforms import Form, validators
from wtforms import Field, TextField, SelectField, TextAreaField, IntegerField, RadioField, BooleanField, SelectMultipleField, FormField, FieldList, ValidationError, HiddenField
from wtforms import widgets 
from flask_wtf import RecaptchaField

from portality.core import app
from portality import models, lcc
from portality.datasets import country_options, language_options, currency_options, main_license_options

blueprint = Blueprint('forms', __name__)


ISSN_REGEX = re.compile(r'^\d{4}-\d{3}(\d|X|x){1}$')
ISSN_ERROR = 'An ISSN or EISSN should be 7 or 8 digits long, separated by a dash, e.g. 1234-5678. If it is 7 digits long, it must end with the letter X (e.g. 1234-567X).'
EMAIL_CONFIRM_ERROR = 'Please double check the email addresses - they do not match.'
URL_REQUIRED_SCHEME_REGEX = re.compile(r'^[a-z]+://([^/:]+\.[a-z]{2,10}|([0-9]{1,3}\.){3}[0-9]{1,3})(:[0-9]+)?(\/.*)?$', re.IGNORECASE)

true_val = 'True'
false_val = 'False'
none_val = 'None'

optional_url_binary_choices = [(false_val, 'No')]
optional_url_binary_choices_optvals = [v[0] for v in optional_url_binary_choices]
binary_choices = [(true_val, 'Yes')] + optional_url_binary_choices

other_val = 'Other'
other_label = other_val
other_choice = (other_val, other_val)
ternary_choices = binary_choices + [other_choice]
optional_url_ternary_choices_optvals = optional_url_binary_choices_optvals  # "No" still makes the URL optional, from ["Yes", "No", "Other"]
ternary_choices_list = [v[0] for v in ternary_choices]

license_options = [
    ('', ''),
    ('CC by', 'Attribution'),
    ('CC by-nc', 'Attribution NonCommercial'),
    ('CC by-nc-nd', 'Attribution NonCommercial NoDerivatives'),
    ('CC by-nc-sa', 'Attribution NonCommercial ShareAlike'),
    ('CC by-nd', 'Attribution NoDerivatives'),
    ('CC by-sa', 'Attribution ShareAlike'),
]

author_pays_options = [
    ('N', 'No charges'),
    ('CON', 'Conditional charges'),
    ('Y', 'Has charges'),
    ('NY', 'No information'),
]

digital_archiving_policy_no_policy_value = "No policy in place"
digital_archiving_policy_specific_library_value = 'A national library'
digital_archiving_policy_specific_library_label = digital_archiving_policy_specific_library_value

digital_archiving_policy_optional_url_choices = [
    (digital_archiving_policy_no_policy_value, digital_archiving_policy_no_policy_value), 
]
digital_archiving_policy_optional_url_choices_optvals = [v[0] for v in digital_archiving_policy_optional_url_choices]

__digital_archiving_policy_choices = [
    ('LOCKSS', 'LOCKSS'), 
    ('CLOCKSS', 'CLOCKSS'), 
    ('Portico', 'Portico'), 
    ('PMC/Europe PMC/PMC Canada', 'PMC/Europe PMC/PMC Canada'), 
    (digital_archiving_policy_specific_library_value, digital_archiving_policy_specific_library_value), 
] + [other_choice]

digital_archiving_policy_choices = digital_archiving_policy_optional_url_choices  + __digital_archiving_policy_choices

digital_archiving_policy_choices_list = [v[0] for v in digital_archiving_policy_choices]

deposit_policy_choices = [
    (none_val, none_val), 
    ('Sherpa/Romeo', 'Sherpa/Romeo'),
    ('Dulcinea', 'Dulcinea'),
    ('OAKlist', 'OAKlist'),
    ('H\xc3\xa9lo\xc3\xafse'.decode('utf-8'), 'H\xc3\xa9lo\xc3\xafse'.decode('utf-8')),
    ('Diadorim', 'Diadorim'),
] + [other_choice]

deposit_policy_choices_list = [v[0] for v in deposit_policy_choices]

license_optional_url_choices = [ ('not-cc-like', 'No') ]
license_optional_url_choices_optvals = [v[0] for v in license_optional_url_choices]

license_choices = main_license_options + license_optional_url_choices + [other_choice]
license_choices_list = [v[0] for v in license_choices]

license_checkbox_choices = [
    ('by', 'Attribution'),
    ('nc', 'No Commercial Usage'),
    ('nd', 'No Derivatives'),
    ('sa', 'Share Alike'),
]

review_process_optional_url_choices_1 = [ ('', ' ') ]
review_process_optional_url_choices_2 = [ (none_val, none_val) ]
review_process_optional_url_choices_optvals = [v[0] for v in review_process_optional_url_choices_1 + review_process_optional_url_choices_2]

review_process_choices = review_process_optional_url_choices_1 + [
    ('Editorial review', 'Editorial review'), 
    ('Peer review', 'Peer review'),
    ('Blind peer review', 'Blind peer review'), 
    ('Double blind peer review', 'Double blind peer review'), 
    ('Open peer review', 'Open peer review'),
] + review_process_optional_url_choices_2

fulltext_format_choices = [
    ('PDF', 'PDF'), 
    ('HTML', 'HTML'), 
    ('ePUB', 'ePUB'), 
    ('XML', 'XML'), 
] + [other_choice]

fulltext_format_choices_list = [v[0] for v in fulltext_format_choices]

article_identifiers_choices = [
    (none_val, none_val),
    ('DOI', 'DOI'),
    ('Handles', 'Handles'),
    ('ARK', 'ARK'),
] + [other_choice]

article_identifiers_choices_list = [v[0] for v in article_identifiers_choices]

application_status_choices_optional_owner = [
    ('', ' '),
    ('pending', 'Pending'),
    ('in progress', 'In progress'),
    ('rejected', 'Rejected'),
]

application_status_choices_editor = application_status_choices_optional_owner + [('ready', "Ready")]

application_status_choices_admin = application_status_choices_editor + [('accepted', 'Accepted')]

application_status_choices_optvals = [v[0] for v in application_status_choices_optional_owner]

suggester_name_validators = [validators.Required()]
suggester_email_validators = [validators.Required(), validators.Email(message='Invalid email address.')]
suggester_email_confirm_validators = [validators.Required(), validators.Email(message='Invalid email address.'), validators.EqualTo('suggester_email', EMAIL_CONFIRM_ERROR)]

def interpret_special(val):
    # if you modify this, make sure to modify reverse_interpret_special as well
    if isinstance(val, basestring):
        if val.lower() == true_val.lower():
            return True
        elif val.lower() == false_val.lower():
            return False
        elif val.lower() == none_val.lower():
            return None
        elif val == digital_archiving_policy_no_policy_value:
            return None

    if isinstance(val, list):
        if len(val) == 1:
            actual_val = interpret_special(val[0])
            if not actual_val:
                return []
            return val

        return val

    return val

def reverse_interpret_special(val, field=''):
    # if you modify this, make sure to modify interpret_special as well

    if val is None:
        return none_val
    elif val is True:
        return true_val
    elif val is False:
        return false_val
    # no need to handle digital archiving policy or other list
    # fields here - empty lists handled below

    if isinstance(val, list):
        if len(val) == 1:
            reverse_actual_val = reverse_interpret_special(val[0], field=field)
            return [reverse_actual_val]
        elif len(val) == 0:
            # mostly it'll just be a None val
            if field == 'digital_archiving_policy':
                return [digital_archiving_policy_no_policy_value]

            return [none_val]

        return val

    return val



def interpret_other(value, other_field_data, other_value=other_val, store_other_label=False):
    '''
    Interpret a value list coming from (e.g.) checkboxes when one of
    them says "Other" and allows free-text input.

    The value can also be a string. In that case, if it matched other_value, other_field_data is returned
    instead of the original value. This is for radio buttons with an "Other" option - you only get 1 value
    from the form, but if it's "Other", you still need to replace it with the relevant free text field data.

    :param value: String or list of values from the form.
        checkboxes_field.data basically.
    :param other_field_data: data from the Other inline extra text input field.
        Usually checkboxes_field_other.data or similar.
    :param other_value: Which checkbox has an extra field? Put its value in here. It's "Other" by default.
        More technically: the value which triggers considering and adding the data in other_field to value.
    '''
    # if you modify this, make sure to modify reverse_interpret_other too
    if isinstance(value, basestring):
        if value == other_value:
            return other_field_data
    elif isinstance(value, list):
        value = value[:]
        # if "Other" (or some custom value) is in the there, remove it and take the data from the extra text field
        if other_value in value and other_field_data:
            # preserve the order, important for reversing this process when displaying the edit form
            where = value.index(other_value)
            if store_other_label:
                # Needed when multiple items in the list could be freely specified,
                # i.e. unrestricted by the choices for that field.
                # Digital archiving policies is such a field, with both an
                # "Other" choice requiring free text input and a "A national library"
                # choice requiring free text input, presumably with the name
                # of the library.
                value[where] = [other_value, other_field_data]
            else:
                value[where] = other_field_data
    # don't know what else to do, just return it as-is
    return value


def reverse_interpret_other(interpreted_value, possible_original_values, other_value=other_val, replace_label=other_label):
    '''
    Returns tuple: (main field value or list of values, other field value)
    '''
    # if you modify this, make sure to modify interpret_other too
    other_field_val = ''

    if isinstance(interpreted_value, basestring):
        # A special case first: where the value is the empty string.
        # In that case, the main field was never submitted (e.g. if it was
        # a choice of "Yes", "No" and "Other", none of those were submitted
        # as an answer - maybe it was an optional field).
        if not interpreted_value:
            return None, None

        # if the stored (a.k.a. interpreted) value is not one of the
        # possible values, then the "Other" option must have been
        # selected during initial submission
        # if so, all we've got to do is swap them
        # so the main field gets a value of "Other" or similar
        # and the secondary (a.k.a. other) field gets the currently
        # stored value - resulting in a form that looks exactly like the
        # one initially submitted
        if interpreted_value not in possible_original_values:
            return other_value, interpreted_value

    elif isinstance(interpreted_value, list):
        # 2 copies of the list needed
        interpreted_value = interpreted_value[:]  # don't modify the original list passed in
        for iv in interpreted_value[:]:  # don't modify the list while iterating over it

            # same deal here, if the original list was ['LOCKSS', 'Other']
            # and the secondary field was 'some other policy'
            # then it would have been interpreted by interpret_other
            # into ['LOCKSS', 'some other policy']
            # so now we need to turn that back into
            # (['LOCKSS', 'Other'], 'some other policy')
            if iv not in possible_original_values:
                where = interpreted_value.index(iv)

                if isinstance(iv, list):
                    # This is a field with two or more choices which require
                    # further specification via free text entry.
                    # If we only recorded the free text values, we wouldn't
                    # be able to tell which one relates to which choice.
                    # E.g. ["some other archiving policy", "Library of Chile"]
                    # does not tell us that "some other archiving policy"
                    # is related to the "Other" field, and "Library of Chile"
                    # is related to the "A national library field.
                    #
                    # [["Other", "some other archiving policy"], ["A national library", "Library of Chile"]]
                    # does tell us that, on the other hand.
                    # It is this case that we are dealing with here.
                    label = iv[0]
                    val = iv[1]
                    if label == replace_label:
                        other_field_val = val
                        interpreted_value[where] = label
                    else:
                        continue
                else:
                    other_field_val = iv
                    interpreted_value[where] = other_value
                    break

    return interpreted_value, other_field_val


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

class OptionalIf(validators.Optional):
    # A validator which makes a field optional if # another field is set
    # and has a truthy value.

    # Additionally, a list of values (optvals) can be specified - if any
    # of those values are present in the other field, this field becomes
    # optional. The other field having a truthy value is then no longer
    # sufficient.
    field_flags = ('display_required_star', )

    def __init__(self, other_field_name, optvals=[], *args, **kwargs):
        self.other_field_name = other_field_name
        self.optvals = optvals
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

    def __init__(self, exclusive_checkbox_value=none_val, message='When you have selected "{exclusive_checkbox_value}" you are not allowed to tick any other checkboxes.', *args, **kwargs):
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

    def __call__(self, form, field):
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
    # Using checkboxes as radio buttons is a Bad Idea (TM). Do not do it,
    # except where it will simplify a 50-field form, k?

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
    # Using checkboxes as radio buttons is a Bad Idea (TM). Do not do it,
    # except where it will simplify a 50-field form, k?

    def __init__(self, role, *args, **kwargs):
        self.role = role
        super(RequiredIfRole, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        if current_user.has_role(self.role):
            super(RequiredIfRole, self).__call__(form, field)

class DisabledTextField(TextField):

    def __call__(self, *args, **kwargs):
        kwargs.setdefault('disabled', True)
        return super(DisabledTextField, self).__call__(*args, **kwargs)


def subjects2str(subjects):
    subject_strings = []
    for sub in subjects:
        subject_strings.append('{term}'.format(term=sub.get('term')))
    return ', '.join(subject_strings)


class JournalInformationForm(Form):
    title = TextField('Journal Title', [validators.Required()])
    url = URLField('URL', [validators.Required(), URLOptionalScheme()])
    alternative_title = TextField('Alternative Title', [validators.Optional()])
    pissn = TextField('Journal ISSN (print version)',
        [OptionalIf('eissn'), validators.Regexp(regex=ISSN_REGEX, message=ISSN_ERROR)],
        description='Only provide the print ISSN if your journal has one, otherwise leave this field blank. Write the ISSN with the hyphen "-" e.g. 1234-4321.',
    )
    eissn = TextField('Journal ISSN (online version)',
        [OptionalIf('pissn'), validators.Regexp(regex=ISSN_REGEX, message=ISSN_ERROR)],
        description='Write the EISSN with the hyphen "-" e.g. 1234-4321.',
    )
    publisher = TextField('Publisher',
        [validators.Required()]
    )
    society_institution = TextField('Society or Institution',
        [validators.Optional()],
        description='The name of the Society or Institution that the journal belongs to',
    )
    platform = TextField('Platform, Host or Aggregator',
        [validators.Optional()],
        description='The name of the platform, host or aggregator of the journal content, e.g. OJS, HighWire Press, EBSCO etc.'
    )
    contact_name = TextField('Name of contact for this journal',
        [validators.Required()],
        description='Somebody who DOAJ can contact about this journal',
    )
    contact_email = TextField('Contact\'s email address',
        [validators.Required(), validators.Email(message='Invalid email address.')]
    )
    confirm_contact_email = TextField('Confirm contact\'s email address',
        [validators.Required(), validators.Email(message='Invalid email address.'), validators.EqualTo('contact_email', EMAIL_CONFIRM_ERROR)]
    )
    country = SelectField('In which country is the publisher of the journal based?',
        [validators.Required()],
        description='Select the country where the publishing company is legally registered',
        choices=country_options,
    )
    processing_charges = RadioField('Does the journal have article processing charges (APCs)?',
        [validators.Required()],
        description = 'If "No" proceed to question below',
        choices = binary_choices
    )
    processing_charges_amount = IntegerField('Amount',
        [OptionalIf('processing_charges', optvals=optional_url_binary_choices_optvals)],
    )
    processing_charges_currency = SelectField('Currency',
        [OptionalIf('processing_charges', optvals=optional_url_binary_choices_optvals)],
        choices = currency_options,
    )

    submission_charges = RadioField('Does the journal have article submission charges?',
        [validators.Required()],
        description = 'If "No" proceed to question below',
        choices = binary_choices
    )
    submission_charges_amount = IntegerField('Amount',
        [OptionalIf('submission_charges', optvals=optional_url_binary_choices_optvals)],
    )
    submission_charges_currency = SelectField('Currency',
        [OptionalIf('submission_charges', optvals=optional_url_binary_choices_optvals)],
        choices = currency_options,
    )
    waiver_policy = RadioField('Does the journal have a waiver policy (for developing country authors etc)?',
        [validators.Required()],
        choices = binary_choices
    )
    waiver_policy_url = URLField('Enter the URL where this information can be found',
        [OptionalIf('waiver_policy', optvals=optional_url_binary_choices_optvals), URLOptionalScheme()]
    )
    digital_archiving_policy = SelectMultipleField('What digital archiving policy does the journal use?',
        [
            validators.Required(),
            ExclusiveCheckbox(digital_archiving_policy_no_policy_value),
            ExtraFieldRequiredIf('digital_archiving_policy_library', reqval=digital_archiving_policy_specific_library_value),
            ExtraFieldRequiredIf('digital_archiving_policy_other', reqval=other_val),
        ],
        description = "Select all that apply. Institutional archives and publishers' own online archives are not valid",
        choices = digital_archiving_policy_choices,
        option_widget=widgets.CheckboxInput(),
        widget=widgets.ListWidget(prefix_label=False)
    )
    digital_archiving_policy_other = TextField('',
    )
    digital_archiving_policy_library = TextField('',
    )
    digital_archiving_policy_url = URLField('Enter the URL where this information can be found',
        [OptionalIf('digital_archiving_policy', optvals=digital_archiving_policy_optional_url_choices_optvals), URLOptionalScheme()],
        description='This field is optional if you have only selected "No policy in place" above',
    )
    crawl_permission = RadioField('Does the journal allow anyone to crawl the full-text of the journal?',
        [validators.Required()],
        choices = binary_choices
    )
    article_identifiers = SelectMultipleField('Which article identifiers does the journal use?',
        [validators.Required(), ExtraFieldRequiredIf('article_identifiers_other', reqval=other_val), ExclusiveCheckbox()],
        choices = article_identifiers_choices,
        option_widget=widgets.CheckboxInput(),
        widget=widgets.ListWidget(prefix_label=False),
    )
    article_identifiers_other = TextField('',
    )
    download_statistics = RadioField('Does the journal provide download statistics?',
        [validators.Required()],
        description = 'If "No" proceed to question below',
        choices = binary_choices
    )
    download_statistics_url = TextField('Enter the URL where this information can be found',
        [validators.Optional()],
    )
    first_fulltext_oa_year = IntegerField('What was the first calendar year in which a complete volume of the journal provided online Open Access content to the Full Text of all articles? (Full Text may be provided as PDFs. Does not apply for new journals.)',
        [validators.Required(), validators.NumberRange(min=1600, max=(datetime.now().year)) ],
        description = 'Use 4 digits for the year, i.e. YYYY format'
    )
    fulltext_format = SelectMultipleField('Please indicate which formats of full text are available',
        [validators.Required(), ExtraFieldRequiredIf('fulltext_format_other', reqval=other_val)],
        description = 'Tick all that apply',
        choices = fulltext_format_choices,
        option_widget=widgets.CheckboxInput(),
        widget=widgets.ListWidget(prefix_label=False)
    )
    fulltext_format_other = TextField('',
    )
    keywords = TagListField('Add keyword(s) that best describe the journal (comma delimited)',
        [validators.Required(), MaxLen(6, message='You can only enter up to {max_len} keywords.')],
        description='Maximum 6'
    )
    languages = SelectMultipleField('Select the language(s) that the Full Text of the articles is published in',
        [validators.Required()],
        choices = language_options,
        description="You can select multiple languages"
    )
    editorial_board_url = URLField('What is the URL for the Editorial Board page?',
        [validators.Required(), URLOptionalScheme()],
        description = 'The journal must have either an editor or an editorial board with at least 5 clearly identifiable members and affiliation information. We may ask for affiliation information and email addresses as part of our checks.'
    )
    review_process = SelectField('Please select the review process for papers',
        [validators.Required()],
        choices = review_process_choices,
        default = '',
    )
    review_process_url = URLField('Enter the URL where this information can be found',
        [OptionalIf('review_process', optvals=review_process_optional_url_choices_optvals), URLOptionalScheme()],
        description = 'This field is optional if you have selected "None" above.'
    )
    aims_scope_url = URLField("What is the URL for the journal's Aims & Scope",
        [validators.Required(), URLOptionalScheme()]
    )
    instructions_authors_url = URLField("What is the URL for the journal's instructions for authors?",
        [validators.Required(), URLOptionalScheme()]
    )
    plagiarism_screening = RadioField('Does the journal have a policy of screening for plagiarism?',
        [validators.Required()],
        description = 'If "No" proceed to question below',
        choices = binary_choices
    )
    plagiarism_screening_url = URLField("Enter the URL where this information can be found",
        [OptionalIf('plagiarism_screening', optvals=optional_url_binary_choices_optvals), URLOptionalScheme()]
    )
    publication_time = IntegerField('What is the average number of weeks between submission and publication?',
        [validators.Required(), validators.NumberRange(min=0, max=53)]
    )
    oa_statement_url = URLField("What is the URL for the journal's Open Access statement?",
        [validators.Required(), URLOptionalScheme()]
    )
    license_embedded = RadioField('Does the journal embed or display simple machine-readable CC licensing information in its articles?',
        [validators.Required()],
        choices = binary_choices,
        description = 'For more information go to <a target="_blank" href="http://wiki.creativecommons.org/CC_REL">http://wiki.creativecommons.org/CC_REL</a><br><br>If "No" proceed to question below.',
    )
    license_embedded_url = URLField("Please provide a URL to an example page with embedded licensing information",
        [OptionalIf('license_embedded', optvals=optional_url_binary_choices_optvals), URLOptionalScheme()]
    )
    license = RadioField('Does the journal allow reuse and remixing of its content, in accordance with a CC license?',
        [validators.Required(), ExtraFieldRequiredIf('license_other', reqval=other_val)],
        choices = license_choices,
        description = 'For more information go to <a href="http://creativecommons.org/licenses/" target="_blank">http://creativecommons.org/licenses/</a>'
    )
    license_other = TextField('',
    )
    license_checkbox = SelectMultipleField('Which of the following does the content require? (Tick all that apply.)',
        choices = license_checkbox_choices,
        option_widget=widgets.CheckboxInput(),
        widget=widgets.ListWidget(prefix_label=False),
    )
    license_url = URLField("Enter the URL on your site where your license terms are stated",
        [validators.Optional(), URLOptionalScheme()]
    )
    open_access = RadioField("Does the journal allow readers to 'read, download, copy, distribute, print, search, or link to the full texts' of its articles?",
        [validators.Required()],
        choices = binary_choices,
        description = 'From the <a href="http://www.budapestopenaccessinitiative.org/read" target="_blank">Budapest Open Access Initiative\'s definition of Open Access</a>',
    )
    deposit_policy = SelectMultipleField('With which deposit policy directory does the journal have a registered deposit policy?',
        [validators.Required(), ExtraFieldRequiredIf('deposit_policy_other', reqval=other_val), ExclusiveCheckbox()],
        description = 'Select all that apply.',
        choices = deposit_policy_choices,
        option_widget=widgets.CheckboxInput(),
        widget=widgets.ListWidget(prefix_label=False)
    )
    deposit_policy_other = TextField('',
    )
    copyright = RadioField('Does the journal allow the author(s) to hold the copyright without restrictions?',
        [validators.Required(), ExtraFieldRequiredIf('copyright_other', reqval=other_val)],
        choices = ternary_choices
    )
    copyright_other = TextField('',
    )
    copyright_url = URLField('Enter the URL where this information can be found',
        [OptionalIf('copyright', optvals=optional_url_ternary_choices_optvals), URLOptionalScheme()]
    )
    publishing_rights = RadioField('Will the journal allow the author(s) to retain publishing rights without restrictions?',
        [validators.Required(), ExtraFieldRequiredIf('publishing_rights_other', reqval=other_val)],
        choices = ternary_choices
    )
    publishing_rights_other = TextField('',
    )
    publishing_rights_url = URLField('Enter the URL where this information can be found',
        [OptionalIf('publishing_rights', optvals=optional_url_ternary_choices_optvals), URLOptionalScheme()]
    )


class NoteForm(Form):
    note = TextAreaField('Note')
    date = DisabledTextField('Date')


class JournalForm(JournalInformationForm):
    author_pays = RadioField('Author pays to publish', [validators.Optional()], choices=author_pays_options)
    author_pays_url = TextField('Author pays - guide link', [validators.Optional(), validators.URL()])
    oa_end_year = IntegerField('Year in which the journal stopped publishing OA content', [validators.Optional(), validators.NumberRange(max=datetime.now().year)])
    notes = FieldList(FormField(NoteForm))
    subject = SelectMultipleField('Subjects', [validators.Optional()], choices=lcc.lcc_choices)
    owner = TextField('Owner', [validators.Required()])
    make_all_fields_optional = BooleanField('Allow incomplete form',
        description='<strong>Only tick this box if:</strong>'
                    '<br>a/ you are editing an old, incomplete record;'
                    '<br>b/ you really, really need to change a value without filling in the whole record;'
                    '<br>c/ <strong>you understand that the system will put in default values like "No" and "None" into old records which are missing some information</strong>.'
    )
    # fields for assigning to editor group
    editor_group = TextField("Editor Group", [validators.Optional()])
    editor = SelectField("Assigned to") # choices to be assigned at form render time


class SuggestionForm(JournalInformationForm):
    articles_last_year = IntegerField('How many research and review articles did the journal publish in the last calendar year?',
        [validators.Required(), validators.NumberRange(min=0)],
        description='A journal must publish at least 5 articles per year to stay in the DOAJ',
    )
    articles_last_year_url = URLField('Enter the URL where this information can be found', 
        [validators.Required(), URLOptionalScheme()]
    )
    metadata_provision = RadioField('Does the journal provide, or intend to provide, article level metadata to DOAJ?',
        [validators.Required()],
        description='For new applications, metadata must be provided within 3 months of acceptance into DOAJ',
        choices=binary_choices
    )
    suggester_name = TextField('Your name',
        suggester_name_validators
    )
    suggester_email = TextField('Your email address', 
        suggester_email_validators
    )
    suggester_email_confirm = TextField('Confirm your email address', 
        suggester_email_confirm_validators
    )

    make_all_fields_optional = BooleanField('Allow incomplete form',
        description='<strong>Only tick this box if:</strong>'
                    '<br>a/ you are editing an old, incomplete record;'
                    '<br>b/ you really, really need to change a value without filling in the whole record;'
                    '<br>c/ <strong>you understand that the system will put in default values like "No" and "None" into old records which are missing some information</strong>.'
    )

    # fields for assigning to editor group
    editor_group = TextField("Editor Group", [validators.Optional()])
    editor = SelectField("Assigned to", default="") # choices to be assigned at form render time


class EditSuggestionForm(SuggestionForm):
    application_status = SelectField('Application Status',
        [validators.Required()],
        # choices = application_status_choices, # choices are late-binding as they depend on the user
        default = '',
        description='Setting this to Accepted will send an email to the'
                    ' owner of the application telling them their journal'
                    ' is now in the DOAJ. The Owner field must not be'
                    ' blank when the status is set to Accepted.'
    )
    notes = FieldList(FormField(NoteForm))
    subject = SelectMultipleField('Subjects', [validators.Optional()], choices=lcc.lcc_choices)
    owner = TextField('Owner',
        [OptionalIf('application_status', optvals=application_status_choices_optvals)],
        description='DOAJ account to which the application belongs to.'
                    '<br><br>'
                    'This field is optional unless the application status is set to Accepted.'
                    '<br><br>'
                    'Entering a non-existent account and setting the application status to Accepted will automatically create the account using the Contact information in Questions 9 & 10, and send an email containing the Contact\'s username + password.'
    )
    #owner = TextField('Owner', [RequiredIfRole("admin")],
    #    description='DOAJ account to which the suggestion belongs to.'
    #                '<br><br>'
    #                'This field is optional unless the application status is set to Accepted.'
    #                '<br><br>'
    #                'Entering a non-existent account and setting the application status to Accepted will automatically create the account using the Contact information in Questions 9 & 10, and send an email containing the Contact\'s username + password.'
    #)

    # overrides
    suggester_name = TextField("Name",
        suggester_name_validators
    )
    suggester_email = TextField("Email address",
        suggester_email_validators
    )
    suggester_email_confirm = TextField("Confirm email address",
        suggester_email_confirm_validators
    )


##########################################################################
## Forms and related features for Article metadata
##########################################################################

DOI_REGEX = "^((http:\/\/){0,1}dx.doi.org/|(http:\/\/){0,1}hdl.handle.net\/|doi:|info:doi:){0,1}(?P<id>10\\..+\/.+)"
DOI_ERROR = 'Invalid DOI.  A DOI can optionally start with a prefix (such as "doi:"), followed by "10." and the remainder of the identifier'

# use the year choices in app.cfg or default to 15 years previous.
start_year = app.config.get("METADATA_START_YEAR", datetime.now().year - 15)

YEAR_CHOICES = [(str(y), str(y)) for y in range(datetime.now().year + 1, start_year, -1)]
MONTH_CHOICES = [("1", "01"), ("2", "02"), ("3", "03"), ("4", "04"), ("5", "05"), ("6", "06"), ("7", "07"), ("8", "08"), ("9", "09"), ("10", "10"), ("11", "11"), ("12", "12")]

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
            raise ValidationError("Either this field or " + other_field.label.text + " is required")

class AuthorForm(Form):
    name = TextField("Name", [validators.Optional()])
    affiliation = TextField("Affiliation", [validators.Optional()])
    
class ArticleForm(Form):
    title = TextField("Article Title", [validators.Required()])
    doi = TextField("DOI", [validators.Optional(), validators.Regexp(regex=DOI_REGEX, message=DOI_ERROR)])
    authors = FieldList(FormField(AuthorForm), min_entries=3) # We have to do the validation for this at a higher level
    abstract = TextAreaField("Abstract", [validators.Optional()])
    keywords = TextField("Keywords", [validators.Optional()], description="Use a , to separate keywords") # enhanced with select2
    fulltext = TextField("Full-Text URL", [validators.Optional(), validators.URL()], description="(The URL for each article must be unique)")
    publication_year = SelectField("Year", [validators.Optional()], choices=YEAR_CHOICES, default=str(datetime.now().year))
    publication_month = SelectField("Month", [validators.Optional()], choices=MONTH_CHOICES, default=str(datetime.now().month) )
    pissn = SelectField("Journal ISSN (print version)", [ThisOrThat("eissn")], choices=[]) # choices set at construction
    eissn = SelectField("Journal ISSN (online version)", [ThisOrThat("pissn")], choices=[]) # choices set at construction
 
    volume = TextField("Volume Number", [validators.Optional()])
    number = TextField("Issue Number", [validators.Optional()])
    start = TextField("Start Page", [validators.Optional()])
    end = TextField("End Page", [validators.Optional()])

    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)
        try:
            if not current_user.is_anonymous():
                issns = models.Journal.issns_by_owner(current_user.id)
                ic = [("", "Select an ISSN")] + [(i,i) for i in issns]
                self.pissn.choices = ic
                self.eissn.choices = ic
        except:
            # not logged in, and current_user is broken
            # probably you are loading the class from the command line
            pass


##########################################################################
## Editor Group Forms
##########################################################################

class UniqueGroupName(object):
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, form, field):
        exists_id = models.EditorGroup.group_exists_by_name(field.data)
        if exists_id is None:
            # if there is no group of the same name, we are fine
            return

        # if there is a group of the same name, we need to check whether it's the
        # same group as we are currently editing
        id_field = form._fields.get("group_id")
        if id_field is None or id_field.data == "" or id_field.data is None:
            # if there is no id field then this is a new group, and so the name clashes
            # with an existing group
            raise validators.ValidationError("The group's name must be unique among the Editor Groups")

        # if we get to here, the id_field exists, so we need to check whether it matches
        # the group with the same id
        if id_field.data != exists_id:
            raise validators.ValidationError("The group's name must be unique among the Editor Groups")

class NotRole(object):
    def __init__(self, role, *args, **kwargs):
        self.role = role

    def __call__(self, form, field):
        accounts = [a.strip() for a in field.data.split(",") if a.strip() != ""]
        if len(accounts) == 0:
            return
        fails = []
        for a in accounts:
            acc = models.Account.pull(a)
            if acc.has_role(self.role) and not acc.is_super:
                fails.append(acc.id)
        if len(fails) == 0:
            return
        have_or_has = "have" if len(fails) > 1 else "has"
        msg = ", ".join(fails) + " " + have_or_has + " role " + self.role + " so cannot be assigned to an Editor Group"
        raise validators.ValidationError(msg)


class EditorGroupForm(Form):
    group_id = HiddenField("Group ID", [validators.Optional()])
    name = TextField("Group Name", [validators.Required(), UniqueGroupName()])
    editor = TextField("Editor", [validators.Required(), NotRole("publisher")])
    associates = TextField("Associate Editors", [validators.Optional(), NotRole("publisher")])


















# a forms overview page at the top level, can list forms or say whatever needs said about forms, or catch closed forms
@blueprint.route('/')
def intro():
    # can add in any auth or admin redirection to closed here if necessary
    return render_template('forms/index.html')
        

# a generic form closed page
@blueprint.route('/closed')
def closed():
    return render_template('forms/closed.html')


# a generic form completion confirmation page
@blueprint.route('/complete')
def complete():
    return render_template('forms/complete.html')


# form handling endpoint, by form name - define more for each form required
@blueprint.route('/<ftype>', methods=['GET','POST'])
def form(ftype='record'):

    # for forms requiring auth, add an auth check here

    klass = getattr(models, ftype[0].capitalize() + ftype[1:] )
    
    if request.method == 'GET':
        # TODO: if people are logged in it may be necessary to render a form with previously submitted data
        response = make_response(
            render_template(
                'forms/template.html', 
                selections={
                    "records": dropdowns(ftype)
                },
                data={} # if this form renders an object in the database, call it and pass it to the template here
            )
        )
        response.headers['Cache-Control'] = 'public, no-cache, no-store, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        return response

    if request.method == 'POST':
        # call whatever sort of model this form is for
        f = klass()
        try:
            # may be useful to define a save from form method for said model
            f.save_from_form(request)
        except:
            # else default behavious is just to overwrite the record
            # you probably want at least some validation here
            for k, v in request.values.items():
                if k not in ['submit']:
                    f.data[k] = v
            f.save()
        return redirect(url_for('.complete'))


# get dropdown info required for the form
def dropdowns(model,key=['name']):
    qry = {
        'query':{'match_all':{}},
        'size': 0,
        'facets':{}
    }
    if not isinstance(key,list):
        key = [key]
    for k in key:
        qry['facets'][k] = {"terms":{"field":k.replace(app.config['FACET_FIELD'],'')+app.config['FACET_FIELD'],"order":'term', "size":100000}}
    vals = []
    try:
        klass = getattr(models, model[0].capitalize() + model[1:] )
        r = klass().query(q=qry)
        for k in key:
            vals = vals + [i.get('term','') for i in r.get('facets',{}).get(k,{}).get("terms",[])]
        return vals
    except:
        return vals



