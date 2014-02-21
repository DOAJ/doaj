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
from wtforms import Field, TextField, SelectField, TextAreaField, IntegerField, RadioField, BooleanField
from wtforms.widgets import TextInput
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


class TagListField(Field):
    widget = TextInput()

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
    keywords = TagListField('Keywords', [validators.Optional()], description='(<strong>use commas</strong> to separate multiple keywords)')
    languages = TagListField('Languages', [validators.Optional()], description='(What languages is the <strong>full text</strong> published in? <strong>Use commas</strong> to separate multiple languages.)')

class JournalForm(JournalInformationForm):
    in_doaj = BooleanField('In DOAJ?')
    provider = TextField('Provider', [validators.Optional()])
    author_pays = RadioField('Author pays to publish', [validators.Required()], choices=author_pays_options)
    author_pays_url = TextField('Author pays - guide link', [validators.Optional(), validators.URL()])
    oa_end_year = IntegerField('Year in which the journal <strong>stopped</strong> publishing OA content', [validators.Optional(), validators.NumberRange(max=datetime.now().year)])




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



