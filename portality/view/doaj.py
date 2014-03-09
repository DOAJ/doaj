from flask import Blueprint, request, abort, make_response, Response
from flask import render_template, abort, redirect, url_for, flash, send_file
from flask.ext.login import current_user
from wtforms import Form, validators
from wtforms import Field, TextField, SelectField, TextAreaField, IntegerField, RadioField
from wtforms.widgets import TextInput
from flask_wtf import RecaptchaField

from portality import dao
from portality import models as models
from portality.core import app
from portality import settings
from portality.view.forms import SuggestionForm

from StringIO import StringIO
import csv
from datetime import datetime
import json
import os, codecs

from concurrent import futures

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

# @blueprint.context_processor
# def additional_context():
#     '''
#     Inserts variables into every template this blueprint renders.  This
#     one deals with the announcement in the header, which can't be built
#     into the template directly, as various styles are applied only if a
#     header is present on the page. It also makes the list of DOAJ
#     sponsors available and may include similar minor pieces of
#     information.
#     '''
#     return {
#         'heading_title': '',
#         'heading_text': '',
#         'sponsors': SPONSORS,
#         'settings': settings,
#         'statistics' : models.JournalArticle.site_statistics()
#         }

@blueprint.route("/")
def home():
    return render_template('doaj/index.html')

@blueprint.route("/search", methods=['GET'])
def search():
    return render_template('doaj/search.html',
               search_page=True,
               facetviews=['journals_and_articles']
           )

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

@blueprint.route("/application/new", methods=["GET", "POST"])
def suggestion():
    form = SuggestionForm(request.form)
    if request.method == 'POST' and form.validate():
        #unicorns
        return redirect(url_for('doaj.suggestion_thanks'))
    return render_template('doaj/suggestion.html', form=form, edit_suggestion_page=True)

@blueprint.route("/application/thanks", methods=["GET"])
def suggestion_thanks():
    return render_template('doaj/suggest_thanks.html')
    

@blueprint.route("/csv")
def csv_data():
    """
    with futures.ProcessPoolExecutor(max_workers=1) as executor:
        result = executor.submit(get_csv_data).result()
    return result
    """
    csv_file = models.Cache.get_latest_csv()
    csv_path = os.path.join(app.config.get("CACHE_DIR"), "csv", csv_file)
    return send_file(csv_path, mimetype="text/csv", as_attachment=True, attachment_filename=csv_file)

"""
def get_csv_data():
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
        csvwriter.writerow([unicode(c).encode("utf8", "replace") if c is not None else "" for c in csv_row])
        csvstring = csvstream.getvalue()
        csvstream.close()
        return csvstring

    thecsv = ''
    thecsv += get_csv_string(models.Journal.CSV_HEADER)

    journal_iterator = models.Journal.all_in_doaj()
    for j in journal_iterator:
        thecsv += get_csv_string(j.csv())

    attachment_name = 'doaj_' + datetime.strftime(datetime.now(), '%Y%m%d_%H%M') + '.csv'
    r = Response(thecsv, mimetype='text/csv', headers={'Content-Disposition':'attachment; filename=' + attachment_name})
    return r
"""

"""
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
"""
    

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

@blueprint.route("/suggest", methods=['GET'])
def suggest():
    return render_template("doaj/suggest.html")
    
@blueprint.route("/supportDoaj")
def support_doaj():
    return render_template("doaj/supportDoaj.html")

@blueprint.route("/support_thanks")
def support_doaj_thanks():
    return render_template("doaj/support_thanks.html")

@blueprint.route("/googlebdb21861de30fe30.html")
def google_webmaster_tools():
    return 'google-site-verification: googlebdb21861de30fe30.html'
