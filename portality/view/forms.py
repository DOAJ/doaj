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
from wtforms import Field, TextField, SelectField, TextAreaField, IntegerField, RadioField, BooleanField, SelectMultipleField
from wtforms import widgets 
from flask_wtf import RecaptchaField

from portality.core import app

import portality.models as models

if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    from portality.ordereddict import OrderedDict
else:
    from collections import OrderedDict

blueprint = Blueprint('forms', __name__)

with open('country-codes.json', 'rb') as f:
    countries = json.loads(f.read())
countries = OrderedDict(sorted(countries.items(), key=lambda x: x[1]['name'])).items()
country_options = [('','')]
country_options_two_char_code_index = []
for code, country_info in countries:
    country_options.append((code, country_info['name']))
    country_options_two_char_code_index.append(code)

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

digital_archiving_policy_choices = [
    ('LOCKSS', 'LOCKSS'), 
    ('CLOCKSS', 'CLOCKSS'), 
    ('Portico', 'Portico'), 
    ('PMC/Europe PMC/PMC Canada', 'PMC/Europe PMC/PMC Canada'), 
    ('No policy in place', 'No policy in place'), 
    ('A national library. Please specify:', 'A national library. Please specify:'), 
    ('Other', 'Other:')
]

binary_choices = [
    ('True', 'Yes'),
    ('False', 'No')
]

ternary_choices = binary_choices + [
    ('Other', 'Other:')
]

deposit_policy_choices = [
    ('Sherpa/Romeo', 'Sherpa/Romeo'),
    ('Dulcinea', 'Dulcinea'),
    ('OAKlist', 'OAKlist'),
    ('H\xc3\xa9loise'.decode('utf-8'), 'H\xc3\xa9loise'.decode('utf-8')),
    ('Diadorum', 'Diadorum'), 
    ('None', 'None'), 
    ('Other:', 'Other:')
]

license_choices = [
    ('CC-BY', 'CC-BY'),
    ('CC-CY SA', 'CC-CY SA'),
    ('CC-BY NC', 'CC-BY NC'),
    ('CC-BY ND', 'CC-BY ND'),
    ('No', 'No'), 
    ('Other:', 'Other:')
]

review_process_choices = [
    ('Editorial review', 'Editorial review'), 
    ('Peer review', 'Peer review'),
    ('Blind peer review', 'Blind peer review'), 
    ('Double blind peer review', 'Double blind peer review'), 
    ('Open peer review', 'Open peer review')
]

fulltext_format_choices = [
    ('PDF', 'PDF'), 
    ('HTML', 'HTML'), 
    ('ePUB', 'ePUB'), 
    ('XML', 'XML'), 
    ('Other:', 'Other:')
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

    def __init__(self, other_field_name, *args, **kwargs):
        self.other_field_name = other_field_name
        super(OptionalIf, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise Exception('no field named "%s" in form' % self.other_field_name)
        if bool(other_field.data):
            super(OptionalIf, self).__call__(form, field)

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
    society_institution = TextField('Society or Institution (if applicable)', 
        [validators.Optional()]
    )
    platform = TextField('Platform, Host or Aggregator (if applicable)', 
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
    submission_charges = RadioField('Does the journal have article submission charges? Include relevant currency.', 
        [validators.Required()],
        description = 'If "Yes" then add the amount (average price) with currency', 
        choices = binary_choices
    )
    journals_last_year = IntegerField('Does the journal have article submission charges? Include relevant currency.', 
        [validators.Required()],
        description = 'Does the journal have article submission charges? Include relevant currency.', 
    )
    journals_last_year_url = TextField('Enter the URL where this information can be found', 
        [validators.Required(), validators.URL()]
    )
    waiver_policy = RadioField('Does the journal have a waiver policy (for developing country authors etc)?', 
        [validators.Required()],
        choices = binary_choices 
    )
    waiver_policy_url = TextField('Enter the URL where this information can be found', 
        [validators.Required(), validators.URL()]
    )
    digital_archiving_policy = SelectMultipleField('What digital archiving policy does the journal use?', 
        [validators.Required()],
        description = "Select all that apply. Institutional archives and publishers' own online archives are not valid",  
        choices = digital_archiving_policy_choices, 
        option_widget=widgets.CheckboxInput(), 
        widget=widgets.ListWidget(prefix_label=False)
    )
    digital_archiving_policy_url = TextField('Enter the URL where this information can be found', 
        [validators.Required(), validators.URL()]
    )
    crawl_permission = RadioField('Does the journal allow anyone to crawl the full-text of the journal?', 
        [validators.Required()],
        choices = binary_choices
    )
    #question 20 should be here
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
        [validators.URL()]
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
    keywords = TagListField('Add keyword(s) that best describe the journal', 
        [validators.Required()], 
        description='MAXIMUM 6'
    )
    languages = TagListField('In which language(s) is the Full Text of articles published? ', 
        [validators.Required()], 
        description="Use ',' (comma) as separator. For example English, French, Spanish."
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
        [validators.Required(), validators.URL()]
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
        [validators.Required(), validators.URL()]
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
        description = 'Please provide an example. For more information go to http://wiki.creativecommons.org/Marking_works '
    )
    license = RadioField('Does the journal allow reuse and remixing of its content, in accordance with a CC-BY, CC-BY-NC, or CC-BY-ND license?', 
        [validators.Required()],
        choices = license_choices, 
        description = 'For more information go to http://creativecommons.org/licenses/ '
    )
    license_url = TextField("Enter the URL on your site where your license terms are stated", 
        [validators.Required(), validators.URL()]
    )
    open_access = RadioField("Does the journal allow readers to 'read, download, copy, distribute, print, search, or link to the full texts' of its articles?", 
        [validators.Required()],
        choices = binary_choices, description = "From the Budapest Open Access Initiative's definition of Open Access: http://www.budapestopenaccessinitiative.org/read "
    )
    deposit_policy = SelectMultipleField('The journal has a deposit policy registered with a deposit policy directory.', 
        [validators.Required()], 
        description = 'Select all that apply.', 
        choices = deposit_policy_choices,
        option_widget=widgets.CheckboxInput(), 
        widget=widgets.ListWidget(prefix_label=False)
    )
    copyright = RadioField('Does the journal allow the author(s) to hold the copyright without restrictions?', 
        [validators.Required()],
        choices = ternary_choices 
    )
    copyright_url = TextField('Enter the URL where this information can be found', 
        [validators.Required(), validators.URL()]
    )
    publishing_rights = RadioField('Will the journal allow the author(s) to retain publishing rights without restrictions?', 
        [validators.Required()], 
        choices = ternary_choices
    )
    publishing_rights_url = TextField('Enter the URL where this information can be found', 
        [validators.Required(), validators.URL()]
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



