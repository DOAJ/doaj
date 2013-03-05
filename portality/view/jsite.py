
# this runs the jsite endpoint for standard display of web pages
# requires there to be a deduplicate endpoint available 

import json
from copy import deepcopy

import requests, urllib, urllib2, markdown
from copy import deepcopy

from flask import Blueprint, request, abort, make_response, render_template
from flask.ext.login import current_user

import portality.util as util
from portality.core import app
import portality.models as models


blueprint = Blueprint('jsite', __name__)


# handles deduplications, does not need a specific routing, just gets passed to from jsite
def deduplicate(path='',duplicates=[],target='/'):
    if current_user.is_anonymous():
        abort(401)
    elif request.method == 'GET':
        jsitem = deepcopy(app.config['JSITE_OPTIONS'])
        jsitem['facetview']['initialsearch'] = False
        return render_template('deduplicate.html', jsite_options=json.dumps(jsitem), duplicates=duplicates, url=target)
    elif request.method == 'POST':
        for k,v in request.values.items():
            if v and k not in ['url', 'submit']:
                if k.startswith('delete_'):
                    rec = models.Record.pull(k.replace('delete_',''))
                    if rec is not None: rec.delete()
                else:
                    rec = models.Record.pull(k)
                    rec.data['url'] = v
                    rec.save()
        if 'url' in request.values: target = request.values['url']
        return redirect(target)


# this is a catch-all that allows us to present everything as a search
@blueprint.route('/', methods=['GET','POST','DELETE'])
@blueprint.route('/<path:path>', methods=['GET','POST','DELETE'])
def jsite(path=''):
    jsite = deepcopy(app.config['JSITE_OPTIONS'])
    if current_user.is_anonymous():
        jsite['loggedin'] = False
    else:
        jsite['loggedin'] = True

    url = '/' + path.lstrip('/').rstrip('/')
    if url == '/': url += 'index'
    if url.endswith('.json'): url = url.replace('.json','')
    rec = models.Record.pull_by_url(url)
        
    # if no record returned by URL check if it is a duplicate
    if not rec:
        duplicates = models.Record.check_duplicate(url)
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
                'id': models.Record.makeid(),
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
            rec = models.Record(**newrecord)
            rec.save()
            jsite['newrecord'] = True
            jsite['data'] = newrecord                
        
        title = ''
        if rec:
            title = rec.data.get('title','')

        return render_template('index.html', content=content, title=title, jsite_options=json.dumps(jsite))

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
                rec = models.Record(**newrec)
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

