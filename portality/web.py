import json

from flask import Flask, jsonify, json, request, redirect, abort, make_response
from flask import render_template, flash
from flask.views import View, MethodView
from flask.ext.login import login_user, current_user

import portality.dao
import portality.util as util
from portality.core import app, login_manager
from portality.view.account import blueprint as account
from portality import auth


app.register_blueprint(account, url_prefix='/account')

@login_manager.user_loader
def load_account_for_login_manager(userid):
    out = portality.dao.Account.get(userid)
    return out

@app.context_processor
def set_current_user():
    """ Set some template context globals. """
    return dict(current_user=current_user)

@app.before_request
def standard_authentication():
    """Check remote_user on a per-request basis."""
    remote_user = request.headers.get('REMOTE_USER', '')
    if remote_user:
        user = portality.dao.Account.get(remote_user)
        if user:
            login_user(user, remember=False)
    # add a check for provision of api key
    elif 'api_key' in request.values:
        res = portality.dao.Account.query(q='api_key:"' + request.values['api_key'] + '"')['hits']['hits']
        if len(res) == 1:
            user = portality.dao.Account.get(res[0]['_source']['id'])
            if user:
                login_user(user, remember=False)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(401)
def page_not_found(e):
    return render_template('401.html'), 401


@app.route('/query/<path:path>', methods=['GET','POST'])
@app.route('/query/', methods=['GET','POST'])
@app.route('/query', methods=['GET','POST'])
def query(path='Record'):
    pathparts = path.split('/')
    subpath = pathparts[0]
    if subpath.lower() == 'account':
        abort(401)
    klass = getattr(portality.dao, subpath[0].capitalize() + subpath[1:] )
    qs = request.query_string
    if request.method == "POST":
        qs += "&source=" + json.dumps(dict(request.form).keys()[-1])
    if len(pathparts) > 1 and pathparts[1] == '_mapping':
        resp = make_response( json.dumps(klass().get_mapping()) )
    else:
        resp = make_response( klass().raw_query(qs) )
    resp.mimetype = "application/json"
    return resp
        

@app.route('/')
def home():
    try:
        res = portality.dao.Record.query(sort={'created_date':{'order':'desc'}})
    except:
        res = portality.dao.Record.query()
    return render_template(
        'home/index.html',
        assemblies = portality.dao.Record.query(terms={'type':'assembly'})['hits']['total'],
        records = portality.dao.Record.query(terms={'type':'part'})['hits']['total'],
        recent = [i['_source'] for i in res['hits']['hits']]
    )


@app.route('/users')
@app.route('/users.json')
def users():
    if current_user.is_anonymous():
        abort(401)
    users = portality.dao.Account.query(sort={'id':{'order':'asc'}},size=1000000)
    if users['hits']['total'] != 0:
        accs = [portality.dao.Account.get(i['_source']['id']) for i in users['hits']['hits']]
        # explicitly mapped to ensure no leakage of sensitive data. augment as necessary
        users = []
        for acc in accs:
            user = {"collections":len(acc.collections),"id":acc["id"]}
            try:
                user['created_date'] = acc['created_date']
                user['description'] = acc['description']
            except:
                pass
            users.append(user)
    if util.request_wants_json():
        resp = make_response( json.dumps(users, sort_keys=True, indent=4) )
        resp.mimetype = "application/json"
        return resp
    else:
        return render_template('account/users.html',users=users)
    

# this is a catch-all that allows us to present everything as a search
# such as /implicit_facet_key/implicit_facet_value
# and any thing else passed as a search
@app.route('/<path:path>', methods=['GET','POST','DELETE'])
def default(path):
    import portality.search
    searcher = portality.search.Search(path=path,current_user=current_user)
    return searcher.find()


if __name__ == "__main__":
    portality.dao.init_db()
    app.run(host='0.0.0.0', debug=app.config['DEBUG'], port=app.config['PORT'])

