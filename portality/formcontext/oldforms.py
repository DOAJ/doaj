import re
from datetime import datetime

from flask import request, make_response, render_template, redirect, url_for
from flask.ext.login import current_user

from wtforms import Form, validators
from wtforms import TextField, SelectField, TextAreaField, IntegerField, RadioField, BooleanField, SelectMultipleField, FormField, FieldList, ValidationError, HiddenField

from portality.core import app
from portality import models, lcc
from portality.datasets import main_license_options

EMAIL_CONFIRM_ERROR = 'Please double check the email addresses - they do not match.'

none_val = "None"
true_val = 'True'
false_val = 'False'

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
    ('CC BY', 'Attribution'),
    ('CC BY-NC', 'Attribution NonCommercial'),
    ('CC BY-NC-ND', 'Attribution NonCommercial NoDerivatives'),
    ('CC BY-NC-SA', 'Attribution NonCommercial ShareAlike'),
    ('CC BY-ND', 'Attribution NoDerivatives'),
    ('CC BY-SA', 'Attribution ShareAlike'),
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
    ('ready', 'Ready')
]

application_status_choices_editor = application_status_choices_optional_owner# + [('ready', "Ready")]

application_status_choices_admin = application_status_choices_editor + [('accepted', 'Accepted')]

application_status_choices_optvals = [v[0] for v in application_status_choices_optional_owner]

suggester_name_validators = [validators.Required()]
suggester_email_validators = [validators.Required(), validators.Email(message='Invalid email address.')]
suggester_email_confirm_validators = [validators.Required(), validators.Email(message='Invalid email address.'), validators.EqualTo('suggester_email', EMAIL_CONFIRM_ERROR)]




def subjects2str(subjects):
    subject_strings = []
    for sub in subjects:
        subject_strings.append('{term}'.format(term=sub.get('term')))
    return ', '.join(subject_strings)










##########################################################################
## Forms and related features for Article metadata
##########################################################################

DOI_REGEX = "^((http:\/\/){0,1}dx.doi.org/|(http:\/\/){0,1}hdl.handle.net\/|doi:|info:doi:){0,1}(?P<id>10\\..+\/.+)"
DOI_ERROR = 'Invalid DOI.  A DOI can optionally start with a prefix (such as "doi:"), followed by "10." and the remainder of the identifier'

# use the year choices in app.cfg or default to 15 years previous.
start_year = app.config.get("METADATA_START_YEAR", datetime.now().year - 15)

YEAR_CHOICES = [(str(y), str(y)) for y in range(datetime.now().year + 1, start_year - 1, -1)]
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
