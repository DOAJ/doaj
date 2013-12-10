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

from portality.view.account import blueprint as account
from portality.view.contact import blueprint as contact
from portality.view.query import blueprint as query
from portality.view.stream import blueprint as stream
from portality.view.forms import blueprint as forms
from portality.view.doaj import blueprint as doaj
from portality.view.oaipmh import blueprint as oaipmh
from portality.view.atom import blueprint as atom

app.register_blueprint(account, url_prefix='/account')
app.register_blueprint(contact, url_prefix='/contact')
app.register_blueprint(query, url_prefix='/query')
app.register_blueprint(stream, url_prefix='/stream')
app.register_blueprint(forms, url_prefix='/forms')
app.register_blueprint(oaipmh)
app.register_blueprint(atom)
app.register_blueprint(doaj)

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
    return redirect("/"), 301

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

