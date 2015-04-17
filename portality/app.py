'''
This is the default app controller for portality.
For inclusion in your own project you should make your own version of this controller
and include the views you require, as well as writing new ones. Of course, views must 
also be backed up by models, so have a look at the example models and use them / write 
new ones as required too.
'''
import os

from flask import request, abort, render_template, redirect, send_file, url_for, flash
from flask.ext.login import login_user, current_user
from copy import deepcopy

from datetime import datetime
import tzlocal
import pytz

import portality.models as models
from portality.core import app, login_manager
from portality import settings
from portality.util import flash_with_url

from portality.view.account import blueprint as account
from portality.view.admin import blueprint as admin
from portality.view.publisher import blueprint as publisher
from portality.view.query import blueprint as query
from portality.view.stream import blueprint as stream
from portality.view.forms import blueprint as forms
from portality.view.doaj import blueprint as doaj
from portality.view.oaipmh import blueprint as oaipmh
from portality.view.openurl import blueprint as openurl
from portality.view.atom import blueprint as atom
from portality.view.editor import blueprint as editor
from portality.view.doajservices import blueprint as services

app.register_blueprint(account, url_prefix='/account')
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(publisher, url_prefix='/publisher')
app.register_blueprint(query, url_prefix='/query')
app.register_blueprint(query, url_prefix="/admin_query")
app.register_blueprint(query, url_prefix="/publisher_query")
app.register_blueprint(query, url_prefix="/editor_query")
app.register_blueprint(query, url_prefix="/associate_query")
app.register_blueprint(query, url_prefix="/publisher_reapp_query")
app.register_blueprint(stream, url_prefix='/stream')
app.register_blueprint(forms, url_prefix='/forms')
app.register_blueprint(editor, url_prefix='/editor')
app.register_blueprint(services, url_prefix='/service')

app.register_blueprint(oaipmh)
app.register_blueprint(openurl)
app.register_blueprint(atom)
app.register_blueprint(doaj)

"""
FIXME: this needs to be sorted out - they shouldn't be in here and in doaj.py, but there is an issue
with the 404 pages which requires them
"""
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
SPONSORS = {
        # the key should correspond to the sponsor logo name in
        # /static/doaj/images/sponsors without the extension for
        # consistency - no code should rely on this though
        'biomed-central': {'name':'BioMed Central', 'logo': 'biomed-central.gif', 'url': 'http://www.biomedcentral.com/'},
        'coaction': {'name': 'Co-Action Publishing', 'logo': 'coaction.gif', 'url': 'http://www.co-action.net/'},
        'cogent-oa': {'name': 'Cogent OA', 'logo': 'cogent-oa.gif', 'url': 'http://cogentoa.com/'},
        'copernicus': {'name': 'Copernicus Publications', 'logo': 'copernicus.gif', 'url': 'http://publications.copernicus.org/'},
        'frontiers': {'name': 'Frontiers', 'logo': 'frontiers.gif', 'url': 'http://www.frontiersin.org/'},
        'hindawi': {'name': 'Hindawi Publishing Corporation', 'logo': 'hindawi.jpg', 'url': 'http://www.hindawi.com/'},
        'lund-university': {'name': 'Lund University', 'logo': 'lund-university.jpg', 'url': 'http://www.lunduniversity.lu.se/'},
        'mdpi': {'name': 'Multidisciplinary Digital Publishing Institute (MDPI)', 'logo': 'mdpi.gif', 'url': 'http://www.mdpi.com/'},
        'springer': {'name': 'Springer Science+Business Media', 'logo': 'springer.gif', 'url': 'http://www.springer.com/'},
        'taylor-and-francis': {'name': 'Taylor and Francis Group', 'logo': 'taylor-and-francis.gif', 'url': 'http://www.taylorandfrancisgroup.com/'},
        'karger-oa': {'name': 'Karger Open Access', 'logo': 'karger-oa.jpg', 'url': 'http://www.karger.com/OpenAccess'},
        'cottage-labs': {'name': 'Cottage Labs LLP', 'logo': 'cottagelabs.gif', 'url': 'http://cottagelabs.com'},
        'wiley': {'name': 'Wiley', 'logo': 'wiley.gif', 'url': 'http://wiley.com'},
        'scielo': {'name': 'SciELO (Scientific Electronic Library Online)', 'logo': 'scielo.jpg', 'url': 'http://www.scielo.br/'},
        'edp-sciences': {'name': 'EDP Sciences', 'logo': 'edp-sciences.gif', 'url': 'http://www.edpsciences.org/'},
        'ebsco': {'name': 'EBSCO Information Services', 'logo': 'ebsco.gif', 'url': 'http://www.ebsco.com/'},
        'sage': {'name': 'SAGE Publications', 'logo': 'sage.gif', 'url': 'http://www.sagepublications.com/'},
        'thieme': {'name': 'Thieme Medical Publishers', 'logo': 'thieme.gif', 'url': 'http://www.thieme.com/'},
        'brill': {'name': 'Brill', 'logo': 'brill.jpg', 'url': 'http://www.brill.com/'},
        'proquest': {'name': 'ProQuest', 'logo': 'proquest.gif', 'url': 'http://www.proquest.com/'},
        'exlibris': {'name': 'ExLibris', 'logo': 'exlibris.gif', 'url': 'http://www.exlibrisgroup.com/'},
        'nature': {'name': 'Nature Publishing Group', 'logo': 'nature.gif', 'url': 'http://www.nature.com/npg_/index_npg.html'},
        'palgrave-macmillan': {'name': 'Palgrave Macmillan', 'logo': 'palgrave-macmillan.gif', 'url': 'http://www.palgrave.com/'},
        'qscience': {'name': 'QScience', 'logo': 'qscience.gif', 'url': 'http://www.qscience.com/'},
        'neurensics': {'name': 'Neurensics', 'logo': 'neurensics.jpg', 'url': 'http://www.neurensics.com/'},
        'journalprep': {'name': 'Journal Prep', 'logo': 'journalprep.jpg', 'url': 'http://www.journalprep.com/?aff=yvubaqyby'},
}
SPONSORS = OrderedDict(sorted(SPONSORS.items(), key=lambda t: t[0])) # create an ordered dictionary, sort by the key of the unordered one

# Redirects from previous DOAJ app.
# RJ: I have decided to put these here so that they can be managed 
# alongside the DOAJ codebase.  I know they could also go into the
# nginx config, but there is a chance that they will get lost or forgotten
# some day, whereas this approach doesn't have that risk.
@app.route("/doaj")
def legacy():
    func = request.values.get("func")
    if func == "csv":
        return redirect(url_for('doaj.csv_data')), 301
    elif func == "rss":
        return redirect(url_for('atom.feed')), 301
    elif func == "browse" or func == 'byPublicationFee  ':
        return redirect(url_for('doaj.search')), 301
    elif func == "openurl":
        vals = request.values.to_dict(flat=True)
        del vals["func"]
        return redirect(url_for('openurl.openurl', **vals), 301)
    abort(404)

@app.route("/doaj2csv")
def another_legacy_csv_route():
    return redirect("/csv"), 301

@app.route("/schemas/doajArticles.xsd")
def legacy_doaj_XML_schema():
    schema_fn = 'doajArticles.xsd'
    return send_file(
            os.path.join(app.config.get("STATIC_DIR"), "doaj", schema_fn),
            mimetype="application/xml", as_attachment=True, attachment_filename=schema_fn
            )

@login_manager.user_loader
def load_account_for_login_manager(userid):
    out = models.Account.pull(userid)
    return out

# FIXME: this used to calculate the site stats on request, but for the time being
# this is an unnecessary overhead, so taking it out.  Will need to put something
# equivalent back in when we do the admin area
@app.context_processor
def set_current_context():
    """ Set some template context globals. """
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
        'statistics' : models.JournalArticle.site_statistics(),
        "current_user": current_user,
        "app" : app
        }
    # return dict(current_user=current_user, app=app)

@app.template_filter('utc_timestamp')
def utc_timestamp(stamp, string_format="%Y-%m-%dT%H:%M:%SZ"):
    """
    Format a local time datetime object to UTC
    :param stamp: a datetime object
    :param string_format: defaults to "%Y-%m-%dT%H:%M:%SZ", which complies with ISO 8601
    :return: the string formatted datetime
    """
    local = tzlocal.get_localzone()
    ld = local.localize(stamp)
    tt = ld.utctimetuple()
    utcdt = datetime(tt.tm_year, tt.tm_mon, tt.tm_mday, tt.tm_hour, tt.tm_min, tt.tm_sec, tzinfo=pytz.utc)
    return utcdt.strftime(string_format)

@app.template_filter('doi_url')
def doi_url(doi):
    """
    Create a link from a DOI.
    :param doi: the string DOI
    :return: the HTML link
    """
    tendot = doi[doi.find('10.'):]
    return "<a href='http://dx.doi.org/{0}'>{0}</a>".format(tendot)

@app.before_request
def standard_authentication():
    """Check remote_user on a per-request basis."""
    remote_user = request.headers.get('REMOTE_USER', '')
    if remote_user:
        user = models.Account.pull(remote_user)
        if user:
            login_user(user, remember=False)
    # add a check for provision of api key
    elif 'api_key' in request.values:
        res = models.Account.query(q='api_key:"' + request.values['api_key'] + '"')['hits']['hits']
        if len(res) == 1:
            user = models.Account.pull(res[0]['_source']['id'])
            if user:
                login_user(user, remember=False)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(401)
def page_not_found(e):
    return render_template('401.html'), 401
        

if __name__ == "__main__":
    pycharm_debug = app.config.get('DEBUG_PYCHARM', False)
    if len(sys.argv) > 1:
        if sys.argv[1] == '-d':
            pycharm_debug = True

    if pycharm_debug:
        app.config['DEBUG'] = False
        import pydevd
        pydevd.settrace(app.config.get('DEBUG_PYCHARM_SERVER', 'localhost'), port=app.config.get('DEBUG_PYCHARM_PORT', 6000), stdoutToServer=True, stderrToServer=True)

    app.run(host='0.0.0.0', debug=app.config['DEBUG'], port=app.config['PORT'])
