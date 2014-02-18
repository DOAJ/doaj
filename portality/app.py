'''
This is the default app controller for portality.
For inclusion in your own project you should make your own version of this controller
and include the views you require, as well as writing new ones. Of course, views must 
also be backed up by models, so have a look at the example models and use them / write 
new ones as required too.
'''

from flask import Flask, request, abort, render_template, redirect
from flask.views import View
from flask.ext.login import login_user, current_user

import portality.models as models
from portality.core import app, login_manager
from portality import settings

from portality.view.account import blueprint as account
from portality.view.admin import blueprint as admin
from portality.view.publisher import blueprint as publisher
from portality.view.query import blueprint as query
from portality.view.stream import blueprint as stream
from portality.view.forms import blueprint as forms
from portality.view.doaj import blueprint as doaj
from portality.view.oaipmh import blueprint as oaipmh
from portality.view.atom import blueprint as atom

app.register_blueprint(account, url_prefix='/account')
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(publisher, url_prefix='/publisher')
app.register_blueprint(query, url_prefix='/query')
app.register_blueprint(query, url_prefix="/admin_query")
app.register_blueprint(query, url_prefix="/publisher_query")
app.register_blueprint(stream, url_prefix='/stream')
app.register_blueprint(forms, url_prefix='/forms')
app.register_blueprint(oaipmh)
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


# Redirects from previous DOAJ app.
# RJ: I have decided to put these here so that they can be managed 
# alongside the DOAJ codebase.  I know they could also go into the
# nginx config, but there is a chance that they will get lost or forgotten
# some day, whereas this approach doesn't have that risk.
@app.route("/doaj")
def legacy():
    func = request.values.get("func")
    if func == "csv":
        return redirect("/csv"), 301
    elif func == "rss":
        return redirect("/feed"), 301
    abort(404)

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
    app.run(host='0.0.0.0', debug=app.config['DEBUG'], port=app.config['PORT'])

