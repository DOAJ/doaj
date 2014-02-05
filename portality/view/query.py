'''
An elasticsearch query pass-through.
Has auth control, so it is better than exposing your ES index directly.
'''

import json, urllib2

from flask import Blueprint, request, abort, make_response
from flask.ext.login import current_user

import portality.models as models
from portality.core import app
import portality.util as util


blueprint = Blueprint('query', __name__)


# pass queries direct to index. POST only for receipt of complex query objects
@blueprint.route('/<path:path>', methods=['GET','POST'])
@blueprint.route('/', methods=['GET','POST'])
@util.jsonp
def query(path='Pages', show_not_in_doaj=False):
    pathparts = path.strip('/').split('/')
    subpath = pathparts[0]

    if ',' in subpath:
        subpaths = subpath.split(',')
        subpaths = [clean_item for clean_item in [item.strip() for item in subpaths] if clean_item]  # strip whitespace
    else:
        subpaths = [subpath]

    if not subpaths:
        abort(400)

    for subpath in subpaths:
        if subpath.lower() in app.config.get('NO_QUERY',[]):
            abort(401)

    modelname = ''
    for s in subpaths:
        modelname += s.capitalize()
    try:
        klass = getattr(models, modelname)
    except:
        abort(404)

    if len(pathparts) > 1 and pathparts[1] == '_mapping':
        resp = make_response( json.dumps(klass().query(endpoint='_mapping')) )
    elif len(pathparts) == 2 and pathparts[1] not in ['_mapping','_search']:
        if request.method == 'POST':
            abort(401)
        else:
            rec = klass().pull(pathparts[1])
            if rec:
                if not current_user.is_anonymous() or (app.config.get('PUBLIC_ACCESSIBLE_JSON',True) and rec.data.get('visible',True) and rec.data.get('accessible',True)):
                    resp = make_response( rec.json )
                else:
                    abort(401)
            else:
                abort(404)
    else:
        if request.method == "POST":
            if request.json:
                qs = request.json
            else:
                qs = dict(request.form).keys()[-1]
        elif 'q' in request.values:
            qs = {'query': {'query_string': { 'query': request.values['q'] }}}
        elif 'source' in request.values:
            qs = json.loads(urllib2.unquote(request.values['source']))
        else: 
            qs = {'query': {'match_all': {}}}

        for item in request.values:
            if item not in ['q','source','callback','_'] and isinstance(qs,dict):
                qs[item] = request.values[item]

        if 'sort' not in qs and app.config.get('DEFAULT_SORT',False):
            if path.lower() in app.config['DEFAULT_SORT'].keys():
                qs['sort'] = app.config['DEFAULT_SORT'][path.lower()]

        if current_user.is_anonymous() and app.config.get('ANONYMOUS_SEARCH_TERMS',False):
            if path.lower() in app.config['ANONYMOUS_SEARCH_TERMS'].keys():
                if 'bool' not in qs['query']:
                    pq = qs['query']
                    qs['query'] = {
                        'bool':{
                            'must': [
                                pq
                            ]
                        }
                    }
                if 'must' not in qs['query']['bool']:
                    qs['query']['bool']['must'] = []
                qs['query']['bool']['must'] = qs['query']['bool']['must'] + app.config['ANONYMOUS_SEARCH_TERMS'][path.lower()]

        # if ONLY articles and/or journals are being requested, apply a
        # filter by default
        terms = None
        if not show_not_in_doaj:
            for s in subpaths:
                if s == 'journal' or s == 'article':
                    terms = {'in_doaj':True}

        resp = make_response( json.dumps(klass().query(q=qs, terms=terms), indent=4) )

    resp.mimetype = "application/json"
    return resp

