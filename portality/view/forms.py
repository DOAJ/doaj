'''
A forms system

Build a form template, build a handler for its submission, receive data from end users
'''
from __future__ import print_function

import json
import sys
import re
from datetime import datetime

from flask import Blueprint, request, abort, make_response, render_template, flash, redirect, url_for
from flask.ext.login import current_user

from wtforms import Form, validators
from wtforms import Field, TextField, SelectField, TextAreaField, IntegerField, RadioField, BooleanField, SelectMultipleField, FormField, FieldList, ValidationError
from wtforms import widgets 
from flask_wtf import RecaptchaField

from portality.core import app
from portality import models
from portality.datasets import country_options, language_options, currency_options

blueprint = Blueprint('forms', __name__)


ISSN_REGEX = re.compile(r'^\d{4}-\d{3}(\d|X|x){1}$')
ISSN_ERROR = 'An ISSN or EISSN should be 7 or 8 digits long, separated by a dash, e.g. 1234-5678. If it is 7 digits long, it must end with the letter X (e.g. 1234-567X).'
EMAIL_CONFIRM_ERROR = 'Please double check the email addresses - they do not match.'

optional_url_binary_choices = [('False', 'No')]
optional_url_binary_choices_optvals = [v[0] for v in optional_url_binary_choices]
binary_choices = [('True', 'Yes')] + optional_url_binary_choices

other_val = 'Other'
other_choice = (other_val, other_val)
ternary_choices = binary_choices + [other_choice]
optional_url_ternary_choices_optvals = optional_url_binary_choices_optvals  # "No" still makes the URL optional, from ["Yes", "No", "Other"]

none_val = 'None'

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

_digital_archiving_policy_no_policy_value = "No policy in place"
_digital_archiving_policy_specific_library_value = 'A national library'

digital_archiving_policy_optional_url_choices = [
    (_digital_archiving_policy_no_policy_value, _digital_archiving_policy_no_policy_value), 
]
digital_archiving_policy_optional_url_choices_optvals = [v[0] for v in digital_archiving_policy_optional_url_choices]

__digital_archiving_policy_choices = [
    ('LOCKSS', 'LOCKSS'), 
    ('CLOCKSS', 'CLOCKSS'), 
    ('Portico', 'Portico'), 
    ('PMC/Europe PMC/PMC Canada', 'PMC/Europe PMC/PMC Canada'), 
    (_digital_archiving_policy_specific_library_value, _digital_archiving_policy_specific_library_value + ':'), 
] + [other_choice]

digital_archiving_policy_choices = digital_archiving_policy_optional_url_choices  + __digital_archiving_policy_choices


deposit_policy_choices = [
    (none_val, none_val), 
    ('Sherpa/Romeo', 'Sherpa/Romeo'),
    ('Dulcinea', 'Dulcinea'),
    ('OAKlist', 'OAKlist'),
    ('H\xc3\xa9loise'.decode('utf-8'), 'H\xc3\xa9loise'.decode('utf-8')),
    ('Diadorum', 'Diadorum'), 
] + [other_choice]


license_optional_url_choices = [ ('not-cc-like', 'No') ]
license_optional_url_choices_optvals = [v[0] for v in license_optional_url_choices]

license_choices = [
    ('cc-by', 'CC-BY'),
    ('cc-by-sa', 'CC-BY-SA'),
    ('cc-by-nc', 'CC-BY-NC'),
    ('cc-by-nd', 'CC-BY-ND'),
    ('cc-by-nc-nd', 'CC-BY-NC-ND'),
] + license_optional_url_choices + [other_choice]

license_checkbox_choices = [
    ('by', 'Attribution'),
    ('sa', 'Share Alike'),
    ('nc', 'No Commercial Usage'),
    ('nd', 'No Derivatives')
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

article_identifiers_choices = [
    (none_val, none_val),
    ('DOI', 'DOI'),
    ('Handles', 'Handles'),
    ('ARK', 'ARK'),
    ('EzID', 'EzID'),
] + [other_choice]

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

    def debug(self, *args):
        if True:  # change this condition to check for self.other_field_name or whatever you want
                  # in order to only get debugging statements for
                  # certain fields, even in a 50-field form
            print(*args) 

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
        #regex = r'^[a-z]+://([^/:]+%s|([0-9]{1,3}\.){3}[0-9]{1,3})(:[0-9]+)?(\/.*)?$' % tld_part
        regex = r'^([a-z]+://){0,1}?([^/:]+%s|([0-9]{1,3}\.){3}[0-9]{1,3})(:[0-9]+)?(\/.*)?$' % tld_part
        super(URLOptionalScheme, self).__init__(regex, re.IGNORECASE, message)

    def __call__(self, form, field):
        message = self.message
        if message is None:
            message = field.gettext('Invalid URL.')

        super(URLOptionalScheme, self).__call__(form, field, message)


class JournalInformationForm(Form):
    
    title = TextField('Journal Title', [validators.Required()])
    url = TextField('URL', [validators.Required(), validators.URL()])
    alternative_title = TextField('Alternative Title', [validators.Optional()])
    pissn = TextField('Journal ISSN', [OptionalIf('eissn'), validators.Regexp(regex=ISSN_REGEX, message=ISSN_ERROR)])
    eissn = TextField('Journal EISSN', [OptionalIf('pissn'), validators.Regexp(regex=ISSN_REGEX, message=ISSN_ERROR)])
    publisher = TextField('Publisher', [validators.Required()])
    oa_start_year = IntegerField('Year in which the journal <strong>started</strong> publishing OA content', [validators.Required(), validators.NumberRange(min=1600)])
    country = SelectField('Country', [validators.Required()], choices=country_options)
    license = SelectField('Creative Commons (CC) License, if any', [validators.Optional()], choices=license_options)
    

class JournalForm(JournalInformationForm):
    in_doaj = BooleanField('In DOAJ?')
    provider = TextField('Provider', [validators.Optional()])
    author_pays = RadioField('Author pays to publish', [validators.Required()], choices=author_pays_options)
    author_pays_url = TextField('Author pays - guide link', [validators.Optional(), validators.URL()])
    oa_end_year = IntegerField('Year in which the journal <strong>stopped</strong> publishing OA content', [validators.Optional(), validators.NumberRange(max=datetime.now().year)])
    keywords = TagListField('Keywords', [validators.Optional()], description='(<strong>use commas</strong> to separate multiple keywords)')
    languages = TagListField('Languages', [validators.Optional()], description='(What languages is the <strong>full text</strong> published in? <strong>Use commas</strong> to separate multiple languages.)')
    
class SuggestionForm(Form):
    title = TextField('Journal Title', [validators.Required()])
    url = TextField('URL', [validators.Required(), URLOptionalScheme()])
    alternative_title = TextField('Alternative Title', [validators.Optional()])
    pissn = TextField('Journal ISSN',
        [OptionalIf('eissn'), validators.Regexp(regex=ISSN_REGEX, message=ISSN_ERROR)],
        description='Please provide either an ISSN or an EISSN, or both. At least one identifier is needed.',
    )
    eissn = TextField('Journal EISSN',
        [OptionalIf('pissn'), validators.Regexp(regex=ISSN_REGEX, message=ISSN_ERROR)],
        description='Please provide either an ISSN or an EISSN, or both. At least one identifier is needed.',
    )
    publisher = TextField('Publisher', [validators.Required()])
    society_institution = TextField('Society or Institution', 
        [validators.Optional()]
    )
    platform = TextField('Platform, Host or Aggregator', 
        [validators.Optional()]
    )
    contact_name = TextField('Name of contact for this journal', 
        [validators.Required()]
    )
    contact_email = TextField('Contact email address', 
        [validators.Required(), validators.Email(message='Invalid email address.')]
    )
    confirm_contact_email = TextField('Confirm contact email address', 
        [validators.Required(), validators.Email(message='Invalid email address.'), validators.EqualTo('contact_email', EMAIL_CONFIRM_ERROR)]
    )
    country = SelectField('Country', [validators.Required()], choices=country_options)
    processing_charges = RadioField('Does the journal have article processing charges (APCs)? Include relevant currency.', 
        [validators.Required()],
        description = 'If "Yes" then add the amount (average price) with currency', 
        choices = binary_choices
    )
    processing_charges_amount = IntegerField('Amount',
        [OptionalIf('processing_charges', optvals=optional_url_binary_choices_optvals)],
    )
    processing_charges_currency = SelectField('Currency',
        [OptionalIf('processing_charges', optvals=optional_url_binary_choices_optvals)],
        choices = currency_options,
    )
    
    submission_charges = RadioField('Does the journal have article submission charges? Include relevant currency.', 
        [validators.Required()],
        description = 'If "Yes" then add the amount (average price) with currency', 
        choices = binary_choices
    )
    submission_charges_amount = IntegerField('Amount', 
        [OptionalIf('submission_charges', optvals=optional_url_binary_choices_optvals)],
    )
    submission_charges_currency = SelectField('Currency',
        [OptionalIf('submission_charges', optvals=optional_url_binary_choices_optvals)],
        choices = currency_options,
    )    
    articles_last_year = IntegerField('How many articles did the journal publish in the last calendar year?', 
        [validators.Required()],
        description = 'A journal must publish at least 5 articles per year to stay in the DOAJ', 
    )
    articles_last_year_url = TextField('Enter the URL where this information can be found', 
        [validators.Required(), URLOptionalScheme()]
    )
    waiver_policy = RadioField('Does the journal have a waiver policy (for developing country authors etc)?', 
        [validators.Required()],
        choices = binary_choices 
    )
    waiver_policy_url = TextField('Enter the URL where this information can be found', 
        [OptionalIf('waiver_policy', optvals=optional_url_binary_choices_optvals), URLOptionalScheme()]
    )
    digital_archiving_policy = SelectMultipleField('What digital archiving policy does the journal use?', 
        [
            validators.Required(),
            ExclusiveCheckbox(_digital_archiving_policy_no_policy_value),
            ExtraFieldRequiredIf('digital_archiving_policy_library', reqval=_digital_archiving_policy_specific_library_value),
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
    digital_archiving_policy_url = TextField('Enter the URL where this information can be found', 
        [OptionalIf('digital_archiving_policy', optvals=digital_archiving_policy_optional_url_choices_optvals), URLOptionalScheme()],
        description='This field is optional if you have only selected "No policy in place" above',
    )
    crawl_permission = RadioField('Does the journal allow anyone to crawl the full-text of the journal?', 
        [validators.Required()],
        choices = binary_choices
    )
    article_identifiers = SelectMultipleField('Which article identifiers does the journal use?', 
        [validators.Required(), ExtraFieldRequiredIf('article_identifiers_other', reqval=other_val), ExclusiveCheckbox()],
        description = 'For example DOIs, Handles, ARK, EzID etc',
        choices = article_identifiers_choices,
        option_widget=widgets.CheckboxInput(),   
        widget=widgets.ListWidget(prefix_label=False),
    )
    article_identifiers_other = TextField('',
    )
    metadata_provision = RadioField('Does the journal provide, or intend to provide, article level metadata to DOAJ?', 
        [validators.Required()],
        description = 'For new applications, metadata must be provided within 3 months of acceptance into DOAJ', 
        choices = binary_choices
    )
    download_statistics = RadioField('Does the journal provide download statistics?', 
        [validators.Required()],
        choices = binary_choices 
    )
    download_statistics_url = TextField('Enter the URL where this information can be found', 
        [validators.Optional()],
    )
    first_fulltext_oa_year = IntegerField('What was the first calendar year in which a complete volume of the journal provided online Open Access content to the Full Text of all articles (Full Text may be provided as PDFs).', 
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
    keywords = TagListField('Add keyword(s) that best describe the journal', 
        [validators.Required()], 
        description='Maximum 6'
    )
    languages = SelectMultipleField('Select the language(s) that the Full Text of the articles is published in', 
        [validators.Required()],
        choices = language_options,
        description="You can select multiple languages"
    )
    editorial_board_url = TextField('What is the URL for the Editorial Board page?', 
        [validators.Required(), URLOptionalScheme()], 
        description = 'The journal must have either an editor or an editorial board with clearly identifiable members including affiliation information and email addresses.'
    ) 
    review_process = SelectField('Please select the review process for papers', 
        [validators.Required()],
        choices = review_process_choices,
    )
    review_process_url = TextField('Enter the URL where this information can be found', 
        [OptionalIf('review_process', optvals=review_process_optional_url_choices_optvals), URLOptionalScheme()],
        description = 'This field is optional if you have selected "None" above.'
    )
    aims_scope_url = TextField("What is the URL for the journal's Aims & Scope", 
        [validators.Required(), URLOptionalScheme()]
    )
    instructions_authors_url = TextField("What is the URL for the journal's instructions for authors?", 
        [validators.Required(), URLOptionalScheme()]
    )
    plagiarism_screening = RadioField('Does the journal have a policy of screening for plagiarism?', 
        [validators.Required()],
        choices = binary_choices 
    )
    plagiarism_screening_url = TextField("Enter the URL where this information can be found", 
        [OptionalIf('plagiarism_screening', optvals=optional_url_binary_choices_optvals), URLOptionalScheme()]
    )
    publication_time = IntegerField('What is the average number of weeks between submission and publication', 
        [validators.Required(), validators.NumberRange(min=0, max=53)]
    )
    oa_statement_url = TextField("What is the URL for the journal's Open Access statement?", 
        [validators.Required(), URLOptionalScheme()]
    )
    license_embedded = RadioField('Does the journal embed machine-readable CC licensing information in its article metadata?', 
        [validators.Required()],
        choices = binary_choices, 
        description = 'For more information go to http://wiki.creativecommons.org/Marking_works ',
    )
    license_embedded_url = TextField("Please provide a URL to an example page with embedded licensing information",
        [OptionalIf('license_embedded', optvals=optional_url_binary_choices_optvals), URLOptionalScheme()]
    )
    license = RadioField('Does the journal allow reuse and remixing of its content, in accordance with a CC-BY, CC-BY-NC, or CC-BY-ND license?', 
        [validators.Required(), ExtraFieldRequiredIf('license_other', reqval=other_val)],
        choices = license_choices, 
        description = 'For more information go to http://creativecommons.org/licenses/ '
    )
    license_other = TextField('',
    )
    license_checkbox = SelectMultipleField('Does it require',
        choices = license_checkbox_choices,
        option_widget=widgets.CheckboxInput(), 
        widget=widgets.ListWidget(prefix_label=False),
    )
    license_url = TextField("Enter the URL on your site where your license terms are stated", 
        [validators.Optional(), URLOptionalScheme()]
    )
    open_access = RadioField("Does the journal allow readers to 'read, download, copy, distribute, print, search, or link to the full texts' of its articles?", 
        [validators.Required()],
        choices = binary_choices, 
        description = "From the Budapest Open Access Initiative's definition of Open Access: http://www.budapestopenaccessinitiative.org/read ",
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
    copyright_url = TextField('Enter the URL where this information can be found', 
        [OptionalIf('copyright', optvals=optional_url_ternary_choices_optvals), URLOptionalScheme()]
    )
    publishing_rights = RadioField('Will the journal allow the author(s) to retain publishing rights without restrictions?', 
        [validators.Required(), ExtraFieldRequiredIf('publishing_rights_other', reqval=other_val)], 
        choices = ternary_choices
    )
    publishing_rights_other = TextField('',
    )
    publishing_rights_url = TextField('Enter the URL where this information can be found', 
        [OptionalIf('publishing_rights', optvals=optional_url_ternary_choices_optvals), URLOptionalScheme()]
    )
    suggester_name = TextField('Your Name', 
        [validators.Required()]
    )
    suggester_email = TextField('Your email address', 
        [validators.Required(), validators.Email(message='Invalid email address.')]
    )
    suggester_email_confirm = TextField('Confirm your email address', 
        [validators.Required(), validators.Email(message='Invalid email address.'), validators.EqualTo('suggester_email', EMAIL_CONFIRM_ERROR)]
    )




##########################################################################
## Forms and related features for Article metadata
##########################################################################

DOI_REGEX = "^((http:\/\/){0,1}dx.doi.org/|(http:\/\/){0,1}hdl.handle.net\/|doi:|info:doi:){0,1}(?P<id>10\\..+\/.+)"
DOI_ERROR = 'Invalid DOI.  A DOI can optionally start with a prefix (such as "doi:"), followed by "10." and the remainder of the identifier'

YEAR_CHOICES = [(str(y), str(y)) for y in range(datetime.now().year + 1, datetime.now().year - 15, -1)]
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
    fulltext = TextField("Full-Text URL", [validators.Optional(), validators.URL()])
    publication_year = SelectField("Year", [validators.Optional()], choices=YEAR_CHOICES, default=str(datetime.now().year))
    publication_month = SelectField("Month", [validators.Optional()], choices=MONTH_CHOICES, default=str(datetime.now().month) )
    pissn = SelectField("Journal ISSN", [ThisOrThat("eissn")], choices=[]) # choices set at construction
    eissn = SelectField("Journal E-ISSN", [ThisOrThat("pissn")], choices=[]) # choices set at construction
 
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



