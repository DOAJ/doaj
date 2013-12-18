from flask import Blueprint, request, abort, make_response, Response
from flask import render_template, abort, redirect, url_for, flash
from flask.ext.login import current_user
from wtforms import Form, validators
from wtforms import Field, TextField, SelectField, TextAreaField, IntegerField, RadioField
from wtforms.widgets import TextInput
from flask_wtf import RecaptchaField

from portality import dao
from portality import models as models
from portality.core import app
from portality import settings

from StringIO import StringIO
import csv
from datetime import datetime
import json
import os, codecs

import sys
try:
    if sys.version_info.major == 2 and sys.version_info.minor < 7:
        from portality.ordereddict import OrderedDict
except AttributeError:
    if sys.version_info[0] == 2 and sys.version_info[1] < 7:
        from portality.ordereddict import OrderedDict
    else:
        from collections import OrderedDict
else:
    from collections import OrderedDict

blueprint = Blueprint('doaj', __name__)

SPONSORS = {
        # the key should correspond to the sponsor logo name in
        # /static/doaj/images/sponsors without the extension for
        # consistency - no code should rely on this though
        'biomed-central': {'name':'BioMed Central', 'logo': 'biomed-central.gif', 'url': 'http://www.biomedcentral.com/'},
        'coaction': {'name': 'Co-Action Publishing', 'logo': 'coaction.gif', 'url': 'http://www.co-action.net/'},
        'cogent-oa': {'name': 'Cogent OA', 'logo': 'cogent-oa.gif', 'url': 'http://cogentoa.com/'},
        'copernicus': {'name': 'Copernicus Publications', 'logo': 'copernicus.gif', 'url': 'http://publications.copernicus.org/'},
        'dovepress': {'name': 'Dove Medical Press', 'logo': 'dovepress.png', 'url': 'http://www.dovepress.com/'},
        'frontiers': {'name': 'Frontiers', 'logo': 'frontiers.gif', 'url': 'http://www.frontiersin.org/'},
        'hindawi': {'name': 'Hindawi Publishing Corporation', 'logo': 'hindawi.jpg', 'url': 'http://www.hindawi.com/'},
        'inasp': {'name': 'International Network for the Availability of Scientific Publications (INASP)', 'logo': 'inasp.png', 'url': 'http://www.inasp.info/'},
        'lund-university': {'name': 'Lund University', 'logo': 'lund-university.jpg', 'url': 'http://www.lunduniversity.lu.se/'},
        'mdpi': {'name': 'Multidisciplinary Digital Publishing Institute (MDPI)', 'logo': 'mdpi.png', 'url': 'http://www.mdpi.com/'},
        'springer': {'name': 'Springer Science+Business Media', 'logo': 'springer.gif', 'url': 'http://www.springer.com/'},
        'taylor-and-francis': {'name': 'Taylor and Francis Group', 'logo': 'taylor-and-francis.gif', 'url': 'http://www.taylorandfrancisgroup.com/'},
}
SPONSORS = OrderedDict(sorted(SPONSORS.items(), key=lambda t: t[0])) # create an ordered dictionary, sort by the key of the unordered one

"""
@blueprint.context_processor
def additional_context():
    '''
    Inserts variables into every template this blueprint renders.  This
    one deals with the announcement in the header, which can't be built
    into the template directly, as various styles are applied only if a
    header is present on the page. It also makes the list of DOAJ
    sponsors available and may include similar minor pieces of
    information.
    '''
    return {
        'heading_title': '',
        'heading_text': '',
        'sponsors': SPONSORS,
        'settings': settings,
        'statistics' : models.JournalArticle.site_statistics()
        }
"""
@blueprint.route("/")
def home():
    return render_template('doaj/index.html')

@blueprint.route("/search", methods=['GET'])
def search():
    return render_template('doaj/search.html')

@blueprint.route("/search", methods=['POST'])
def search_post():
    if request.form.get('origin') != 'ui':
        abort(501)  # not implemented

    terms = {'_type': []}
    if request.form.get('include_journals') and request.form.get('include_articles'):
        terms = {}  # the default anyway
    elif request.form.get('include_journals'):
        terms['_type'].append('journal')
    elif request.form.get('include_articles'):
        terms['_type'].append('article')

    qobj = dao.DomainObject.make_query(q=request.form.get('q'), terms=terms)
    return redirect(url_for('.search') + '?source=' + json.dumps(qobj))  # can't pass source as keyword param to url_for as usual, will urlencode the query object

@blueprint.route("/csv")
def csv_data():
    def get_csv_string(csv_row):
        '''
        csv.writer only writes to files - it'd be a lot easier if it
        could give us the string it generates, but it can't. This
        function uses StringIO to capture every CSV row that csv.writer
        produces and returns it.

        :param csv_row: A list of strings, each representing a CSV cell.
            This is the format required by csv.writer .
        '''
        csvstream = StringIO()
        csvwriter = csv.writer(csvstream, quoting=csv.QUOTE_ALL)
        # normalise the row - None -> "", and unicode > 128 to ascii
        csvwriter.writerow([c.encode("ascii", "replace") if c is not None else "" for c in csv_row])
        csvstring = csvstream.getvalue()
        csvstream.close()
        return csvstring

    journal_iterator = models.Journal.all_in_doaj()
    def generate():
        '''Return the CSV header and then all the journals one by one.'''

        '''
        The header will only be generated once. This is because once the
        generator yields a value for the first time, it remembers what
        state its local variables were in. The next time yield is
        called, it can simply resume where it left off. In this
        function, this means that once we get into the loop iterating
        over all the journals, we stay there until we run out of
        journals. So the code before the loop only ever gets executed
        once - the first time the generator returns a value.
        '''
        yield get_csv_string(models.Journal.CSV_HEADER)

        for j in journal_iterator:
            # jm = models.Journal(**j['_source'])
            yield get_csv_string(j.csv())

    #if journals['hits']['total'] > 0:
    #    journals = journals['hits']['hits']
    #else:
    #    return 'Cannot find any journals in the DOAJ index. Please report this problem to ' + settings.ADMIN_EMAIL, 500

    attachment_name = 'doaj_' + datetime.strftime(datetime.now(), '%Y%m%d_%H%M') + '.csv'
    r = Response(generate(), mimetype='text/csv', headers={'Content-Disposition':'attachment; filename=' + attachment_name})
    return r

@blueprint.route("/uploadFile", methods=["GET", "POST"])
@blueprint.route("/uploadfile", methods=["GET", "POST"])
def upload_file():
    if request.method == "GET":
        return render_template('doaj/members/uploadfile.html')
    
    # otherwise we are dealing with a POST - file upload
    f = request.files.get("file")
    publisher = request.values.get("publisher_username")
    
    # do some validation
    if f.filename == "" or publisher is None or publisher == "":
        return render_template('doaj/members/uploadfile.html', no_file=(f.filename == ""), no_publisher=(publisher is None or publisher == ""))
    
    # prep a record to go into the index, to record this upload
    record = models.FileUpload()
    record.upload(f.filename, publisher)
    record.set_id()
    
    # the two file paths that we are going to write to
    txt = os.path.join(app.config.get("UPLOAD_DIR", "."), record.id + ".txt")
    xml = os.path.join(app.config.get("UPLOAD_DIR", "."), record.id + ".xml")
    
    # make the content of the txt metadata file
    metadata = publisher + "\n" + f.filename
    
    # save the metadata to the text file
    with codecs.open(txt, "wb", "utf8") as mdf:
        mdf.write(metadata)
    
    # write the incoming file out to the XML file
    f.save(xml)
    
    # finally, save the index entry
    record.save()
    
    # return the thank you page
    return render_template("doaj/members/upload_thanks.html")
    
    

###############################################################
## The various static endpoints
###############################################################

@blueprint.route("/about")
def about():
    return render_template('doaj/about.html')

@blueprint.route("/contact")
def contact():
    return render_template("doaj/contact.html")

@blueprint.route("/publishers")
def publishers():
    return render_template('doaj/publishers.html')

@blueprint.route("/faq")
def faq():
    return render_template("doaj/faq.html")

@blueprint.route("/features")
def features():
    return render_template("doaj/features.html")

@blueprint.route("/oainfo")
def oainfo():
    return render_template("doaj/oainfo.html")

@blueprint.route("/members")
def members():
    return render_template("doaj/members.html")

@blueprint.route("/membership")
def membership():
    return render_template("doaj/membership.html")

@blueprint.route("/sponsors")
def sponsors():
    return render_template("doaj/our_sponsors.html")

@blueprint.route("/support")
def support():
    return render_template("doaj/support.html")

@blueprint.route("/publishermembers")
def publishermembers():
    return render_template("doaj/publishermembers.html")

@blueprint.route("/suggest", methods=['GET', 'POST'])
def suggest():
    with open('country-codes.json', 'rb') as f:
        countries = json.loads(f.read())
    countries = OrderedDict(sorted(countries.items(), key=lambda x: x[1]['name']))
    country_options = [('','')]
    for code, country_info in countries.items():
        country_options.append((code, country_info['name']))

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
    ]

    class TagListField(Field):
        widget = TextInput()
    
        def _value(self):
            if self.data:
                return u', '.join(self.data)
            else:
                return u''
    
        def process_formdata(self, valuelist):
            if valuelist:
                self.data = [clean_x for clean_x in [x.strip() for x in valuelist[0].split(',')] if clean_x]
            else:
                self.data = []

    class IntegerAsStringField(Field):
        widget = TextInput()
    
        def _value(self):
            if self.data:
                return unicode(str(self.data))
            return u''

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

    issn_error = "The identifier (ISSN or EISSN) should be 7 or 8 digits long, separated by a dash, e.g. 1234-5678. If the identifier is 7 digits long, it must end with the letter X (e.g. 1234-567X)."
    class RegistrationForm(Form):
        url = TextField('URL', [validators.Required()])
        title = TextField('Journal Title', [validators.Required()])
        # TODO either ISSN or EISSN required!
        pissn = TextField('Journal ISSN', [OptionalIf('eissn'), validators.Regexp(r'^\d{4}-\d{3}(\d|X|x){1}$', message=issn_error)])
        eissn = TextField('Journal EISSN', [OptionalIf('pissn'), validators.Regexp(r'^\d{4}-\d{3}(\d|X|x){1}$', message=issn_error)])
        publisher = TextField('Publisher', [validators.Required()])
        oa_start_year = IntegerAsStringField('Start year since online full text content is available', [validators.Required(), validators.NumberRange(min=1600)])
        country = SelectField('Country', [validators.Required()], choices=country_options)
        license = SelectField('Creative Commons (CC) License, if any', [validators.Optional()], choices=license_options)
        author_pays = RadioField('Author pays to publish', [validators.Required()], choices=author_pays_options)
        author_pays_url = TextField('Author pays - guide link', [validators.Optional()])
        journal_contact_name = TextField('Journal Contact name', [validators.Required()])
        journal_contact_email = TextField('Journal Contact email', [validators.Required(), validators.Email()])
        description = TextAreaField('Description', [validators.Optional()])
        keywords = TagListField('Keywords', [validators.Optional()], description='(<strong>use commas</strong> to separate multiple keywords)')
        languages = TagListField('Languages', [validators.Optional()], description='(What languages is the <strong>full text</strong> published in? <strong>Use commas</strong> to separate multiple languages.)')
        submitter_name = TextField('Your name', [validators.Required()])
        submitter_email = TextField('Your email', [validators.Required(), validators.Email()])
        recaptcha = RecaptchaField()

    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        ns = models.Suggestion()
        ns.bibjson().add_url(form.url.data, 'homepage')
        ns.bibjson().title = form.title.data
        ns.bibjson().add_identifier(ns.bibjson().P_ISSN, form.pissn.data)
        ns.bibjson().add_identifier(ns.bibjson().E_ISSN, form.eissn.data)
        ns.bibjson().publisher = form.publisher.data
        ns.bibjson().set_oa_start(year=form.oa_start_year.data)
        ns.bibjson().country = form.country.data
        ns.bibjson().set_license(license_title=form.license.data, license_type=form.license.data)
        ns.bibjson().author_pays = form.author_pays.data
        ns.bibjson().author_pays_url = form.author_pays_url.data
        ns.add_contact(form.journal_contact_name.data, form.journal_contact_email.data)
        ns.bibjson().set_keywords(form.keywords.data)
        ns.bibjson().set_language(form.languages.data)
        ns.description = form.description.data
        ns.set_suggester(form.submitter_name.data, form.submitter_email.data)
        ns.suggested_by_owner = True
        ns.set_in_doaj(False)
        ns.suggested_on = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        ns.save()
        return render_template("doaj/suggest_thanks.html")
    return render_template("doaj/suggest.html", form=form)
    
@blueprint.route("/supportDoaj")
def support_doaj():
    return render_template("doaj/supportDoaj.html")
