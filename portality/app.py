# -*- coding: UTF-8 -*-

"""
This is the default app controller for portality.
For inclusion in your own project you should make your own version of this controller
and include the views you require, as well as writing new ones. Of course, views must
also be backed up by models, so have a look at the example models and use them / write
new ones as required too.
"""
import os, sys
import tzlocal
import pytz
import yaml

from flask import request, abort, render_template, redirect, send_file, url_for, jsonify, send_from_directory
from flask_login import login_user, current_user

from datetime import datetime
from collections import OrderedDict

import portality.models as models
from portality.core import app, es_connection, initialise_index
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
from portality.view.jct import blueprint as jct
from portality.view.apply import blueprint as apply
if 'api1' in app.config['FEATURES']:
    from portality.view.api_v1 import blueprint as api_v1
if 'api2' in app.config['FEATURES']:
    from portality.view.api_v2 import blueprint as api_v2
from portality.view.status import blueprint as status
from portality.lib.normalise import normalise_doi

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
if 'api1' in app.config['FEATURES']:
    app.register_blueprint(api_v1, url_prefix='/api/v1')
if 'api2' in app.config['FEATURES']:
    app.register_blueprint(api_v2, url_prefix='/api/v2')
app.register_blueprint(status, url_prefix='/status')
app.register_blueprint(apply, url_prefix='/apply')
app.register_blueprint(status, url_prefix='/_status')
app.register_blueprint(jct, url_prefix="/jct")

app.register_blueprint(oaipmh)
app.register_blueprint(openurl)
app.register_blueprint(atom)
app.register_blueprint(doaj)

# initialise the index - don't put into if __name__ == '__main__' block,
# because that does not run if gunicorn is loading the app, as opposed
# to the app being run directly by python portality/app.py
# putting it here ensures it will run under any web server
initialise_index(app, es_connection)

# Import list of Sponsors from the static site’s data file
# Only display gold & silver sponsors for now on the homepage
# The same file is used to display sponsors in the Sponsors page’s full list
with open(os.path.join(app.config["BASE_FILE_PATH"],"../static_content/_data/sponsors.yml")) as f:
    SPONSORS = yaml.load(f, Loader=yaml.FullLoader)

with open(os.path.join(app.config["BASE_FILE_PATH"],"../static_content/_data/volunteers.yml")) as f:
    VOLUNTEERS = yaml.load(f, Loader=yaml.FullLoader)

# serve static files from multiple potential locations
# this allows us to override the standard static file handling with our own dynamic version
@app.route("/static/<path:filename>")
@app.route("/static_content/<path:filename>")
def our_static(filename):
    return custom_static(filename)


def custom_static(path):
    for dir in app.config.get("STATIC_PATHS", []):
        target = os.path.join(app.root_path, dir, path)
        if os.path.isfile(target):
            return send_from_directory(os.path.dirname(target), os.path.basename(target))
    abort(404)


# Configure the Google Analytics tracker
from portality.lib import analytics
try:
    analytics.create_logfile(app.config.get('GOOGLE_ANALTYICS_LOG_DIR', None))
    analytics.create_tracker(app.config['GOOGLE_ANALYTICS_ID'], app.config['BASE_DOMAIN'])
except KeyError:
    err = "No Google Analytics credentials found. Required: 'GOOGLE_ANALYTICS_ID' and 'BASE_DOMAIN'."
    if app.config.get("DOAJENV") == 'production':
        app.logger.error(err)
    else:
        app.logger.debug(err)
except analytics.GAException as e:
    app.logger.debug('Unable to send events to Google Analytics: ' + str(e))

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

@app.route("/isCrossrefLoaded")
def is_crossref_loaded():
    if app.config.get("LOAD_CROSSREF_THREAD") is not None and app.config.get("LOAD_CROSSREF_THREAD").isAlive():
        return "false"
    else:
        return "true"

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
        'volunteers': VOLUNTEERS,
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

    try:
        return "https://doi.org/" + normalise_doi(doi)
    except ValueError:
        return ""




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
        if val is True or (isinstance(val, str) and val.lower() == "true"):
            return "Yes"
        elif val is False or (isinstance(val, str) and val.lower() == "false"):
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
    elif 'api_key' in request.values:
        q = models.Account.query(q='api_key:"' + request.values['api_key'] + '"')
        if 'hits' in q:
            res = q['hits']['hits']
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

if 'api2' in app.config['FEATURES']:
    @app.route('/api2/')
    def api_directory():
        return jsonify(
            {
                'api_versions': [
                    {
                        'version': '2.0.0',
                        'base_url': url_for('api_v2.api_spec', _external=True, _scheme=app.config.get('PREFERRED_URL_SCHEME', 'https')),
                        'note': 'Second version of the DOAJ API',
                        'docs_url': url_for('api_v2.docs', _external=True, _scheme=app.config.get('PREFERRED_URL_SCHEME', 'https'))
                    }
                ]
            }
        )


@app.errorhandler(400)
def page_not_found(e):
    return render_template('400.html'), 400

@app.errorhandler(401)
def page_not_found(e):
    return render_template('401.html'), 401

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500

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
