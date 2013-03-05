'''
This is the default app controller for portality.
For inclusion in your own project you should make your own version of this controller
and include the views you require, as well as writing new ones. Of course, views must 
also be backed up by models, so have a look at the example models and use them / write 
new ones as required too.
'''

from flask import Flask, request, abort, render_template
from flask.views import View
from flask.ext.login import login_user, current_user

import portality.models as models
from portality.core import app, login_manager

from portality.view.wikipedia import wikiparse
from portality.view.account import blueprint as account
from portality.view.sitemap import blueprint as sitemap
from portality.view.tagging import blueprint as tagging
from portality.view.media import blueprint as media
from portality.view.admin import blueprint as admin
from portality.view.graph import blueprint as graph
from portality.view.contact import blueprint as contact
from portality.view.query import blueprint as query
from portality.view.stream import blueprint as stream
from portality.view.package import blueprint as package
from portality.view.padthru import blueprint as padthru
from portality.view.search import blueprint as search
from portality.view.jsite import blueprint as jsite


app.register_blueprint(account, url_prefix='/account')
app.register_blueprint(sitemap, url_prefix='/sitemap')
app.register_blueprint(tagging, url_prefix='/tagging')
app.register_blueprint(media, url_prefix='/media')
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(graph, url_prefix='/graph')
app.register_blueprint(contact, url_prefix='/contact')
app.register_blueprint(query, url_prefix='/query')
app.register_blueprint(stream, url_prefix='/stream')
app.register_blueprint(package, url_prefix='/package')
app.register_blueprint(padthru, url_prefix='/padthru')
app.register_blueprint(search, url_prefix='/search')
app.register_blueprint(jsite)


@login_manager.user_loader
def load_account_for_login_manager(userid):
    out = models.Account.pull(userid)
    return out

@app.context_processor
def set_current_context():
    """ Set some template context globals. """
    return dict(current_user=current_user, app=app)

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

