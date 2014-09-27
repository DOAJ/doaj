import re
from datetime import datetime

from wtforms import Form, validators
from wtforms import TextField, SelectField, TextAreaField, IntegerField, RadioField, BooleanField, SelectMultipleField, FormField, FieldList, ValidationError, HiddenField
from wtforms import widgets

from portality.formcontext.fields import URLField, TagListField
from portality.formcontext.validate import URLOptionalScheme, OptionalIf, ExclusiveCheckbox, ExtraFieldRequiredIf, MaxLen
from portality.datasets import country_options, language_options, currency_options, main_license_options

ISSN_REGEX = re.compile(r'^\d{4}-\d{3}(\d|X|x){1}$')
ISSN_ERROR = 'An ISSN or EISSN should be 7 or 8 digits long, separated by a dash, e.g. 1234-5678. If it is 7 digits long, it must end with the letter X (e.g. 1234-567X).'
EMAIL_CONFIRM_ERROR = 'Please double check the email addresses - they do not match.'

none_val = "None"
true_val = 'True'
false_val = 'False'

other_val = 'Other'
other_label = other_val
other_choice = (other_val, other_val)

optional_url_binary_choices = [(false_val, 'No')]
optional_url_binary_choices_optvals = [v[0] for v in optional_url_binary_choices]
binary_choices = [(true_val, 'Yes')] + optional_url_binary_choices

ternary_choices = binary_choices + [other_choice]
optional_url_ternary_choices_optvals = optional_url_binary_choices_optvals  # "No" still makes the URL optional, from ["Yes", "No", "Other"]
ternary_choices_list = [v[0] for v in ternary_choices]

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


article_identifiers_choices = [
    (none_val, none_val),
    ('DOI', 'DOI'),
    ('Handles', 'Handles'),
    ('ARK', 'ARK'),
] + [other_choice]
article_identifiers_choices_list = [v[0] for v in article_identifiers_choices]


fulltext_format_choices = [
    ('PDF', 'PDF'),
    ('HTML', 'HTML'),
    ('ePUB', 'ePUB'),
    ('XML', 'XML'),
] + [other_choice]
fulltext_format_choices_list = [v[0] for v in fulltext_format_choices]


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

license_optional_url_choices = [ ('Not CC-like', 'No') ]
license_optional_url_choices_optvals = [v[0] for v in license_optional_url_choices]
license_choices = main_license_options + license_optional_url_choices + [other_choice]
license_choices_list = [v[0] for v in license_choices]
license_checkbox_choices = [
    ('BY', 'Attribution'),
    ('NC', 'No Commercial Usage'),
    ('ND', 'No Derivatives'),
    ('SA', 'Share Alike'),
]


deposit_policy_choices = [
    (none_val, none_val),
    ('Sherpa/Romeo', 'Sherpa/Romeo'),
    ('Dulcinea', 'Dulcinea'),
    ('OAKlist', 'OAKlist'),
    ('H\xc3\xa9lo\xc3\xafse'.decode('utf-8'), 'H\xc3\xa9lo\xc3\xafse'.decode('utf-8')),
    ('Diadorim', 'Diadorim'),
] + [other_choice]


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