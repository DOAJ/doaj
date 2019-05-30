# -*- coding: UTF-8 -*-

"""
This is the default app controller for portality.
For inclusion in your own project you should make your own version of this controller
and include the views you require, as well as writing new ones. Of course, views must
also be backed up by models, so have a look at the example models and use them / write
new ones as required too.
"""
import os, sys

from flask import request, abort, render_template, redirect, send_file, url_for, jsonify
from flask_login import login_user, current_user

from datetime import datetime
import tzlocal
import pytz

import portality.models as models
from portality.core import app, initialise_index
from portality import settings

from portality.view.account import blueprint as account
from portality.view.admin import blueprint as admin
from portality.view.publisher import blueprint as publisher
from portality.view.query import blueprint as query
from portality.view.doaj import blueprint as doaj
from portality.view.oaipmh import blueprint as oaipmh
from portality.view.openurl import blueprint as openurl
from portality.view.atom import blueprint as atom
from portality.view.editor import blueprint as editor
from portality.view.doajservices import blueprint as services
if 'api' in app.config['FEATURES']:
    from portality.view.api_v1 import blueprint as api_v1
from portality.view.status import blueprint as status

app.register_blueprint(account, url_prefix='/account')
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(publisher, url_prefix='/publisher')
app.register_blueprint(query, url_prefix='/query')
app.register_blueprint(query, url_prefix="/admin_query")
app.register_blueprint(query, url_prefix="/publisher_query")
app.register_blueprint(query, url_prefix="/editor_query")
app.register_blueprint(query, url_prefix="/associate_query")
app.register_blueprint(editor, url_prefix='/editor')
app.register_blueprint(services, url_prefix='/service')
if 'api' in app.config['FEATURES']:
    app.register_blueprint(api_v1, url_prefix='/api/v1')
app.register_blueprint(status, url_prefix='/status')

app.register_blueprint(oaipmh)
app.register_blueprint(openurl)
app.register_blueprint(atom)
app.register_blueprint(doaj)

# initialise the index - don't put into if __name__ == '__main__' block,
# because that does not run if gunicorn is loading the app, as opposed
# to the app being run directly by python portality/app.py
# putting it here ensures it will run under any web server
initialise_index(app)

"""
FIXME: this needs to be sorted out - they shouldn't be in here and in doaj.py, but there is an issue
with the 404 pages which requires them
"""
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

# The key should correspond to the sponsor logo name in /static/doaj/images/sponsors without the extension for
# consistency - no code should rely on this though. Sponsors are in tiers: gold, silver, bronze, and patron.
# Only gold sponsors appear on the front page, and patrons are displayed text-only on the sponsors page alongside
# the other tiers' logos.
SPONSORS = {
    'gold': {
        'ebsco': {'name': 'EBSCO', 'logo': 'ebsco.svg', 'url': 'https://www.ebsco.com/'}
    },
    'silver': {
        'frontiers': {'name': 'Frontiers', 'logo': 'frontiers.png', 'url': 'https://www.frontiersin.org'},
        #'hindawi': {'name': 'Hindawi Publishing Corporation', 'logo': 'hindawi.png', 'url': 'https://www.hindawi.com'},
        'mdpi': {'name': 'Multidisciplinary Digital Publishing Institute (MDPI)', 'logo': 'mdpi.svg', 'url': 'http://www.mdpi.com/'},
        'oclc': {'name': 'OCLC', 'logo': 'oclc.svg', 'url': 'https://www.oclc.org/en-europe/home.html'},
        #'plos': {'name': 'PLOS (Public Library of Science)', 'logo': 'plos.svg', 'url': 'https://www.plos.org/'},
        'springer-nature': {'name': 'Springer Nature', 'logo': 'springer-nature.svg', 'url': 'https://www.springernature.com/gp/group/aboutus'},
        'ufm': {'name': 'Danish Agency for Science and Higher Education', 'logo': 'ufm.svg', 'url': 'https://ufm.dk/'},
        'kbse': {'name': 'National Library of Sweden', 'logo': 'kbse.svg', 'url': 'https://www.kb.se/'},
        'finnish-learned-soc': {'name': 'Federation of Finnish Learned Societies', 'logo': 'finnish-tsvlogo.svg', 'url': 'https://tsv.fi/en/frontpage'},
        'nsd': {'name': 'NSD (Norwegian Centre for Research Data)', 'logo': 'nsd.svg', 'url': 'http://www.nsd.uib.no/nsd/english/index.html'},
        'swedish-research': {'name': 'Swedish Research Council', 'logo': 'swedish-research.svg', 'url': 'https://vr.se/english.html'},
        'digital-science': {'name': 'Digital Science', 'logo': 'digital-science.svg', 'url': 'https://www.digital-science.com'},
        'copernicus': {'name': 'Copernicus Publications', 'logo': 'copernicus.svg', 'url': 'https://publications.copernicus.org/'},
    },
    'bronze': {
        '1science': {'name': '1science', 'logo': '1science.svg', 'url': 'https://1science.com/'},
        'aps': {'name': 'American Physical Society', 'logo': 'aps.gif', 'url': 'https://journals.aps.org/'},
        #'chaoxing': {'name': 'Chaoxing', 'logo': 'chaoxing.jpg', 'url': 'https://www.chaoxing.com'},
        'cottage-labs': {'name': 'Cottage Labs LLP', 'logo': 'cottagelabs.svg', 'url': 'https://cottagelabs.com'},
        'issn': {'name': 'ISSN (International Standard Serial Number)', 'logo': 'issn.jpg', 'url': 'http://www.issn.org/'},
        'lund': {'name': 'Lund University', 'logo': 'lund-university.jpg', 'url': 'https://www.lunduniversity.lu.se/'},
        'sage': {'name': 'SAGE Publications', 'logo': 'sage.svg', 'url': 'http://www.sagepublications.com/'},
        'scielo': {'name': 'SciELO (Scientific Electronic Library Online)', 'logo': 'scielo.svg', 'url': 'http://www.scielo.br/'},
        'taylor-and-francis': {'name': 'Taylor and Francis Group', 'logo': 'taylor-and-francis.svg', 'url': 'http://www.taylorandfrancisgroup.com/'},
        'wiley': {'name': 'Wiley', 'logo': 'wiley.svg', 'url': 'https://wiley.com'},
        'emerald': {'name': 'Emerald Publishing', 'logo': 'emerald.svg', 'url': 'http://emeraldpublishing.com/'},
        'thieme': {'name': 'Thieme Medical Publishers', 'logo': 'thieme.svg', 'url': 'https://www.thieme.com'},
        #'tec-mx': {'name': u'Tecnológico de Monterrey', 'logo': 'tec-mx.png', 'url': 'https://tec.mx/es'},
        #'brill': {'name': 'BRILL', 'logo': 'brill.jpg', 'url': 'https://brill.com/'},
        'ubiquity': {'name': 'Ubiquity Press', 'logo': 'ubiquity_press.svg', 'url': 'https://www.ubiquitypress.com/'},
        #'openedition': {'name': 'Open Edition', 'logo': 'open_edition.svg', 'url': 'https://www.openedition.org'},
        'iop': {"name": "IOP Publishing", "logo": "iop.jpg", "url": "http://ioppublishing.org/"},
        'degruyter': {'name': 'De Gruyter', 'logo': 'degruyter.jpg', 'url': 'https://www.degruyter.com/dg/page/open-access'},
        'rsc': {'name': 'Royal Society of Chemistry', 'logo': 'rsc.svg', 'url': 'https://www.rsc.org'},
        'edp': {'name': 'EDP Sciences', 'logo': 'edp.gif', 'url': 'https://www.edpsciences.org'},
    },
    'patron': {
        #'elife': {'name': 'eLife Sciences Publications', 'logo': 'elife.jpg', 'url': 'https://elifesciences.org'},
        #'karger-oa': {'name': 'Karger Open Access', 'logo': 'karger-oa.svg', 'url': 'https://www.karger.com/OpenAccess'},
        #'enago': {'name': 'ENAGO', 'url': 'https://www.enago.com/'},
    }
}

# In each tier, create an ordered dictionary sorted alphabetically by sponsor name
SPONSORS = {k: OrderedDict(sorted(v.items(), key=lambda t: t[0])) for k, v in SPONSORS.items()}


# Configure the Google Analytics tracker
from portality.lib import analytics
try:
    analytics.create_logfile(app.config.get('GOOGLE_ANALTYICS_LOG_DIR', None))
    analytics.create_tracker(app.config['GOOGLE_ANALYTICS_ID'], app.config['BASE_DOMAIN'])
except (KeyError, analytics.GAException):
    err = "No Google Analytics credentials found. Required: 'GOOGLE_ANALYTICS_ID' and 'BASE_DOMAIN'."
    if app.config.get("DOAJENV") == 'production':
        app.logger.error(err)
    else:
        app.logger.debug(err)


@app.route("/schemas/doajArticles.xsd")
def legacy_doaj_XML_schema():
    schema_fn = 'doajArticles.xsd'
    return send_file(
            os.path.join(app.config.get("STATIC_DIR"), "doaj", schema_fn),
            mimetype="application/xml", as_attachment=True, attachment_filename=schema_fn
            )


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
        'sponsors': SPONSORS,
        'settings': settings,
        'statistics': models.JournalArticle.site_statistics(),
        "current_user": current_user,
        "app": app,
        "current_year": datetime.now().strftime('%Y'),
        }


@app.template_filter("bytesToFilesize")
def bytes_to_filesize(size):
    units = ["bytes", "Kb", "Mb", "Gb"]
    scale = 0
    while size > 1000 and scale < len(units):
        size = float(size) / 1000.0     # note that it is no longer 1024
        scale += 1
    return "{size:.1f}{unit}".format(size=size, unit=units[scale])

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
    return "<a href='https://doi.org/{0}'>{0}</a>".format(tendot)


@app.template_filter('form_diff_table_comparison_value')
def form_diff_table_comparison_value(val):
    """
    Function for converting the given value to a suitable UI value for presentation in the diff table
    on the admin forms for update requests.

    :param val: the raw value to be converted to a display value
    :return:
    """
    if val is None:
        return ""
    if isinstance(val, list) and len(val) == 0:
        return ""

    if isinstance(val, list):
        dvals = []
        for v in val:
            dvals.append(form_diff_table_comparison_value(v))
        return ", ".join(dvals)
    else:
        if val is True or (isinstance(val, basestring) and val.lower() == "true"):
            return "Yes"
        elif val is False or (isinstance(val, basestring) and val.lower() == "false"):
            return "No"
        return val


@app.template_filter('form_diff_table_subject_expand')
def form_diff_table_subject_expand(val):
    """
    Function for expanding one or more subject classifications out to their full terms

    :param val:
    :return:
    """
    if val is None:
        return ""
    if isinstance(val, list) and len(val) == 0:
        return ""
    if not isinstance(val, list):
        val = [val]

    from portality import lcc

    results = []
    for v in val:
        if v is None or v == "":
            continue
        expanded = lcc.lcc_index_by_code.get(v)
        if expanded is not None:
            results.append(expanded + " [code: " + v + "]")
        else:
            results.append(v)

    return ", ".join(results)


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


if 'api' in app.config['FEATURES']:
    @app.route('/api/')
    def api_directory():
        return jsonify(
            {
                'api_versions': [
                    {
                        'version': '1.0.0',
                        'base_url': url_for('api_v1.api_spec', _external=True, _scheme=app.config.get('PREFERRED_URL_SCHEME', 'https')),
                        'note': 'First version of the DOAJ API',
                        'docs_url': url_for('api_v1.docs', _external=True, _scheme=app.config.get('PREFERRED_URL_SCHEME', 'https'))
                    }
                ]
            }
        )


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

    app.run(host=app.config['HOST'], debug=app.config['DEBUG'], port=app.config['PORT'])
