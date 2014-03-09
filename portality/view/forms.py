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
from wtforms import Field, TextField, SelectField, TextAreaField, IntegerField, RadioField, BooleanField, SelectMultipleField, FormField, FieldList, ValidationError
from wtforms import widgets 
from flask_wtf import RecaptchaField

from portality.core import app
from portality import models
from portality.datasets import country_options, language_options, currency_options

blueprint = Blueprint('forms', __name__)


ISSN_REGEX = re.compile(r'^\d{4}-\d{3}(\d|X|x){1}$')
ISSN_ERROR = 'An ISSN or EISSN should be 7 or 8 digits long, separated by a dash, e.g. 1234-5678. If it is 7 digits long, it must end with the letter X (e.g. 1234-567X).'

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

__digital_archiving_policy_choices_1 = [
    ('LOCKSS', 'LOCKSS'), 
    ('CLOCKSS', 'CLOCKSS'), 
    ('Portico', 'Portico'), 
    ('PMC/Europe PMC/PMC Canada', 'PMC/Europe PMC/PMC Canada'), 
]

digital_archiving_policy_optional_url_choices = [
    ('No policy in place', 'No policy in place'), 
]

digital_archiving_policy_optional_url_choices_optvals = [v[0] for v in digital_archiving_policy_optional_url_choices]

__digital_archiving_policy_choices_2 = [
    ('A national library. Please specify', 'A national library. Please specify:'), 
    ('Other', 'Other')
]

digital_archiving_policy_choices = __digital_archiving_policy_choices_1 + digital_archiving_policy_optional_url_choices + __digital_archiving_policy_choices_2

optional_url_binary_choices = [('False', 'No')]
optional_url_binary_choices_optvals = [v[0] for v in optional_url_binary_choices]
binary_choices = [('True', 'Yes')] + optional_url_binary_choices

ternary_choices = binary_choices + [
    ('Other', 'Other')
]

deposit_policy_choices = [
    ('Sherpa/Romeo', 'Sherpa/Romeo'),
    ('Dulcinea', 'Dulcinea'),
    ('OAKlist', 'OAKlist'),
    ('H\xc3\xa9loise'.decode('utf-8'), 'H\xc3\xa9loise'.decode('utf-8')),
    ('Diadorum', 'Diadorum'), 
    ('None', 'None'), 
    ('Other', 'Other')
]

license_choices = [
    ('cc-by', 'CC-BY'),
    ('cc-by-sa', 'CC-BY-SA'),
    ('cc-by-nc', 'CC-BY-NC'),
    ('cc-by-nd', 'CC-BY-ND'),
    ('cc-by-nc-nd', 'CC-BY-NC-ND'),
    ('not-cc', 'No'), 
    ('other', 'Other')
]

license_checkbox_choices = [
    ('by', 'Attribution'),
    ('sa', 'Share Alike'),
    ('nc', 'No Commercial Usage'),
    ('nd', 'No Derivatives')
]

review_process_choices = [
    ('', ' '),
    ('Editorial review', 'Editorial review'), 
    ('Peer review', 'Peer review'),
    ('Blind peer review', 'Blind peer review'), 
    ('Double blind peer review', 'Double blind peer review'), 
    ('Open peer review', 'Open peer review'),
    (False, 'None')
]

fulltext_format_choices = [
    ('PDF', 'PDF'), 
    ('HTML', 'HTML'), 
    ('ePUB', 'ePUB'), 
    ('XML', 'XML'), 
    ('Other', 'Other')
]

article_identifiers_choices = [
    ('DOI', 'DOI'),
    ('Handles', 'Handles'),
    ('ARK', 'ARK'),
    ('EzID', 'EzID'),
    ('None', 'None'),
    ('Other', 'Other')
]

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
    # a validator which makes a field optional if
    # another field is set and has a truthy value

    def __init__(self, other_field_name, optvals=[], *args, **kwargs):
        self.other_field_name = other_field_name
        self.optvals = optvals
        super(OptionalIf, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise Exception('no field named "%s" in form' % self.other_field_name)

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
                raise validators.StopValidation('This field is required')

    def __make_optional(self, form, field):
        super(OptionalIf, self).__call__(form, field)
        raise validators.StopValidation()

class JournalInformationForm(Form):
    
    url = TextField('URL', [validators.Required(), validators.URL()])
    title = TextField('Journal Title', [validators.Required()])
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
    
class SuggestionForm(JournalInformationForm):
    society_institution = TextField('Society or Institution', 
        [validators.Optional()]
    )
    platform = TextField('Platform, Host or Aggregator', 
        [validators.Optional()]
    )
    contact_name = TextField('Name of contact for this journal', 
        [validators.Optional()]
    )
    contact_email = TextField('Contact email', 
        [validators.Required(), validators.Email(message='Invalid email address.')]
    )
    confirm_contact_email = TextField('Confirm email', 
        [validators.Required(), validators.Email(message='Invalid email address.')]
    ) #must match contact_email
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
        [validators.Required(), validators.URL()]
    )
    waiver_policy = RadioField('Does the journal have a waiver policy (for developing country authors etc)?', 
        [validators.Required()],
        choices = binary_choices 
    )
    waiver_policy_url = TextField('Enter the URL where this information can be found', 
        [OptionalIf('waiver_policy', optvals=optional_url_binary_choices_optvals), validators.URL()]
    )
    digital_archiving_policy = SelectMultipleField('What digital archiving policy does the journal use?', 
        [validators.Required()],
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
        [OptionalIf('digital_archiving_policy', optvals=digital_archiving_policy_optional_url_choices_optvals), validators.URL()],
        description='This field is optional if you have only selected "No policy in place" above',
    )
    crawl_permission = RadioField('Does the journal allow anyone to crawl the full-text of the journal?', 
        [validators.Required()],
        choices = binary_choices
    )
    article_identifiers = SelectMultipleField('Which article identifiers does the journal use?', 
        [validators.Required()],
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
        [OptionalIf('download_statistics', optvals=optional_url_binary_choices_optvals)],
    )
    first_fulltext_oa_year = IntegerField('What was the first calendar year in which a complete volume of the journal provided online Open Access content to the Full Text of all articles (Full Text may be provided as PDFs).', 
        [validators.Required()], #TODO: validator for the year
        description = 'Use format YYYY'
    )
    fulltext_format = SelectMultipleField('Please indicate which formats of full text are available', 
        [validators.Required()],
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
    languages = SelectMultipleField('In which language(s) is the Full Text of articles published? ', 
        [validators.Required()],
        choices = language_options,
        description="You can select multiple languages"
    )
    editorial_board_url = TextField('What is the URL for the Editorial Board page?', 
        [validators.Required(), validators.URL()], 
        description = 'The journal must have either an editor or an editorial board with clearly identifiable members including affiliation information and email addresses.'
    ) 
    review_process = SelectField('Please select the review process for papers', 
        [validators.Required()],
        choices = review_process_choices
    )
    review_process_url = TextField('Enter the URL where this information can be found', 
        [OptionalIf('review_process'), validators.URL()]
    )
    aims_scope_url = TextField("What is the URL for the journal's Aims & Scope", 
        [validators.Required(), validators.URL()]
    )
    instructions_authors_url = TextField("What is the URL for the journal's instructions for authors?", 
        [validators.Required(), validators.URL()]
    )
    plagiarism_screening = RadioField('Does the journal have a policy of screening for plagiarism?', 
        [validators.Required()],
        choices = binary_choices 
    )
    plagiarism_screening_url = TextField("Enter the URL where this information can be found", 
        [OptionalIf('plagiarism_screening', optvals=optional_url_binary_choices_optvals), validators.URL()]
    )
    publication_time = IntegerField('What is the average number of weeks between submission and publication', 
        [validators.Required()]
    )
    oa_statement_url = TextField("What is the URL for the journal's Open Access statement?", 
        [validators.Required(), validators.URL()]
    )
    license_embedded = RadioField('Does the journal embed machine-readable CC licensing information in its article metadata?', 
        [validators.Required()],
        choices = binary_choices, 
        description = 'For more information go to http://wiki.creativecommons.org/Marking_works ',
    )
    license_embedded_url = TextField("Please provide a URL to an example page with embedded licensing information",
        [OptionalIf('license_embedded', optvals=optional_url_binary_choices_optvals), validators.URL()]
    )
    license = RadioField('Does the journal allow reuse and remixing of its content, in accordance with a CC-BY, CC-BY-NC, or CC-BY-ND license?', 
        [validators.Required()],
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
        [OptionalIf('license'), validators.URL()]
    )
    open_access = RadioField("Does the journal allow readers to 'read, download, copy, distribute, print, search, or link to the full texts' of its articles?", 
        [validators.Required()],
        choices = binary_choices, 
        description = "From the Budapest Open Access Initiative's definition of Open Access: http://www.budapestopenaccessinitiative.org/read ",
    )
    deposit_policy = SelectMultipleField('Whit which deposit policy directory does the journal have a registered deposit policy?', 
        [validators.Required()], 
        description = 'Select all that apply.', 
        choices = deposit_policy_choices,
        option_widget=widgets.CheckboxInput(), 
        widget=widgets.ListWidget(prefix_label=False)
    )
    deposit_policy_other = TextField('',
    )
    copyright = RadioField('Does the journal allow the author(s) to hold the copyright without restrictions?', 
        [validators.Required()],
        choices = ternary_choices 
    )
    copyright_other = TextField('',
    )
    copyright_url = TextField('Enter the URL where this information can be found', 
        [OptionalIf('copyright'), validators.URL()]
    )
    publishing_rights = RadioField('Will the journal allow the author(s) to retain publishing rights without restrictions?', 
        [validators.Required()], 
        choices = ternary_choices
    )
    publishing_rights_other = TextField('',
    )
    publishing_rights_url = TextField('Enter the URL where this information can be found', 
        [OptionalIf('publishing_rights'), validators.URL()]
    )
    suggester_name = TextField('Your Name', 
        [validators.Required()]
    )
    suggester_email = TextField('Your email address', 
        [validators.Required(), validators.Email(message='Invalid email address.')]
    )
    suggester_email_confirm = TextField('Confirm your email address', 
        [validators.Required(), validators.Email(message='Invalid email address.')]
    ) #must match suggester_email




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



