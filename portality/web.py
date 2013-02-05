'''
This is the default app controller for portality.
For inclusion in your own project you should make your own version of this controller
and include the views you require, as well as writing new ones. Of course, views must 
also be backed up by models, so have a look at the example models and use them / write 
new ones as required too.
'''

import re, json, requests, urllib, urllib2, markdown
from copy import deepcopy

from flask import Flask, jsonify, json, request, redirect, abort, make_response
from flask import render_template, flash
from flask.views import View, MethodView
from flask.ext.login import login_user, current_user

import portality.dao as dao
import portality.util as util
from portality.core import app, login_manager
from portality import auth

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
from portality.view.deduplicate import blueprint as deduplicate
from portality.view.package import blueprint as package
from portality.view.padthru import blueprint as padthru


app.register_blueprint(account, url_prefix='/account')
app.register_blueprint(sitemap, url_prefix='/sitemap')
app.register_blueprint(tagging, url_prefix='/tagging')
app.register_blueprint(media, url_prefix='/media')
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(graph, url_prefix='/graph')
app.register_blueprint(contact, url_prefix='/contact')
app.register_blueprint(query, url_prefix='/query')
app.register_blueprint(stream, url_prefix='/stream')
app.register_blueprint(deduplicate, url_prefix='/deduplicate')
app.register_blueprint(package, url_prefix='/package')
app.register_blueprint(padthru, url_prefix='/padthru')


@login_manager.user_loader
def load_account_for_login_manager(userid):
    out = dao.Account.pull(userid)
    return out

@app.context_processor
def set_current_user():
    """ Set some template context globals. """
    return dict(current_user=current_user, sharethis=app.config.get('JSITE_OPTIONS',[]).get('sharethis',False))

@app.before_request
def standard_authentication():
    """Check remote_user on a per-request basis."""
    remote_user = request.headers.get('REMOTE_USER', '')
    if remote_user:
        user = dao.Account.pull(remote_user)
        if user:
            login_user(user, remember=False)
    # add a check for provision of api key
    elif 'api_key' in request.values:
        res = dao.Account.query(q='api_key:"' + request.values['api_key'] + '"')['hits']['hits']
        if len(res) == 1:
            user = dao.Account.pull(res[0]['_source']['id'])
            if user:
                login_user(user, remember=False)


@app.errorhandler(404)
def page_not_found(e):
    jsitem = deepcopy(app.config['JSITE_OPTIONS'])
    jsitem['facetview']['initialsearch'] = False
    return render_template('404.html', jsite_options=json.dumps(jsitem)), 404

@app.errorhandler(401)
def page_not_found(e):
    jsitem = deepcopy(app.config['JSITE_OPTIONS'])
    jsitem['facetview']['initialsearch'] = False
    return render_template('401.html', jsite_options=json.dumps(jsitem)), 401
        

# this is a catch-all that allows us to present everything as a search
@app.route('/', methods=['GET','POST','DELETE'])
@app.route('/<path:path>', methods=['GET','POST','DELETE'])
def default(path=''):
    jsite = deepcopy(app.config['JSITE_OPTIONS'])
    if current_user.is_anonymous():
        jsite['loggedin'] = False
    else:
        jsite['loggedin'] = True

    url = '/' + path.lstrip('/').rstrip('/')
    if url == '/': url += 'index'
    if url.endswith('.json'): url = url.replace('.json','')
    rec = dao.Record.pull_by_url(url)
        
    # if no record returned by URL check if it is a duplicate
    if not rec:
        duplicates = dao.Record.check_duplicate(url)
        if duplicates and not current_user.is_anonymous():
            return deduplicate(path,duplicates,url)
        elif duplicates:
            abort(404)

    if request.method == 'GET':
        if util.request_wants_json():
            if not rec or current_user.is_anonymous():
                abort(404)
            resp = make_response( rec.json )
            resp.mimetype = "application/json"
            return resp

        content = ''

        # build the content
        if rec:

            if not rec.data.get('accessible',False) and current_user.is_anonymous():
                abort(401)

            # update content from collaborative pad
            if jsite['collaborative'] and not rec.get('decoupled',False):
                c = requests.get('http://pads.cottagelabs.com/p/' + rec.id + '/export/txt')
                if rec.data.get('content',False) != c.text:
                    rec.data['content'] = c.text
                    rec.save()
            content += markdown.markdown( rec.data.get('content','') )

            # if an embedded file url has been provided, embed it in the content too
            if rec.data.get('embed', False):
                if rec.data['embed'].find('/pub?') != -1 or rec.data['embed'].find('docs.google.com') != -1:
                    content += '<iframe id="embedded" src="' + rec.data['embed'] + '" width="100%" height="1000" style="border:none;"></iframe>'
                else:
                    content += '<iframe id="embedded" src="http://docs.google.com/viewer?url=' + urllib.quote_plus(rec.data['embed']) + '&embedded=true" width="100%" height="1000" style="border:none;"></iframe>'
            
            # remove the content box from the js to save load - it is built separately
            jsite['data'] = rec.data
            del jsite['data']['content']

        elif current_user.is_anonymous():
            abort(404)
        else:
            # create a new record for a new page here
            newrecord = {
                'id': dao.makeid(),
                'url': url,
                'title': url.split('/')[-1],
                'author': current_user.id,
                'content': '',
                'comments': False,
                'embed': '',
                'visible': False,
                'accessible': True,
                'editable': True,
                'image': '',
                'excerpt': '',
                'tags': [],
            }
            rec = dao.Record(**newrecord)
            rec.save()
            jsite['newrecord'] = True
            jsite['data'] = newrecord                
        
        title = ''
        if rec:
            title = rec.data.get('title','')

        # if on the /search page, wire in the search everything box to the displayed search results
        search = False
        if url == '/search':
            search = True

        return render_template('index.html', content=content, title=title, search=search, jsite_options=json.dumps(jsite), offline=jsite['offline'])

    elif request.method == 'POST':
        if rec:
            if not rec.data.get('accessible',False) and current_user.is_anonymous():
                abort(401)
            else:
                # content is not always sent, to save transmission size. If not there, don't overwrite it to blank
                newdata = request.json
                if 'content' not in newdata: newdata['content'] = rec.data['content']
                rec.data = newdata
        else:
            if current_user.is_anonymous():
                abort(401)
            else:
                newrec = request.json
                rec = dao.Record(**newrec)
        rec.save()
        resp = make_response( rec.json )
        resp.mimetype = "application/json"
        return resp
    
    elif request.method == 'DELETE':
        if current_user.is_anonymous():
            abort(401)
        try:
            rec.delete()
            return ""
        except:
            abort(404)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=app.config['DEBUG'], port=app.config['PORT'])

