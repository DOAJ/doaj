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
def query(path='Pages'):
    pathparts = path.strip('/').split('/')
    subpath = pathparts[0]

    if ',' in subpath:
        subpaths = subpath.split(',')
        subpaths = [clean_item for clean_item in [item.strip() for item in subpaths] if clean_item]  # strip whitespace
    else:
        subpaths = [subpath]

    if not subpaths:
        abort(400)
    
    # first, decide if we are to 401 the request
    for subpath in subpaths:
        if subpath.lower() in app.config.get('NO_QUERY',[]):
            abort(401)
        if subpath.lower() in app.config.get("SU_ONLY", []):
            if current_user.is_anonymous() or not current_user.is_super:
                abort(401)
    
    # now look at the config of this route and determine if the url path
    # requires us to limit access or not to a user role
    #
    owner_filter = False # don't apply the owner filter unless expressly requested
    default_filter = True # always apply the default filter unless asked otherwise
    role = None
    qr = app.config.get("QUERY_ROUTE", {})
    frag = request.path
    for qroute in qr:
        if frag.startswith("/" + qroute):
            default_filter = qr[qroute].get("default_filter", True)
            role = qr[qroute].get("role")
            owner_filter = qr[qroute].get("owner_filter")
            break
    
    # if there is a role, then check that the user is not anonymous and
    # that the user has the required role
    if role is not None:
        if current_user.is_anonymous() or not current_user.has_role(role):
            abort(401)
    
    # if we get to here, then we are good to respond, though check further down
    # to see if we apply the default filter
    
    modelname = ''
    for s in subpaths:
        modelname += s.capitalize()

    klass = models.lookup_model(modelname, capitalize=False)
    if not klass:
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
        # filter by default, unless the user should be allowed to see
        # all records
        terms = {}
        """
        if current_user.is_anonymous() or (request.referrer is not None and "/search?" in request.referrer): # FIXME: hardcoded for the time being - should probably be configurable
            terms = _default_filter(subpaths)
        else:
            if not current_user.has_role("view_not_in_doaj"):
                terms = _default_filter(subpaths)
        """
        if default_filter:
            terms.update(_default_filter(subpaths))
        
        if owner_filter:
            terms.update(_owner_filter())
        
        resp = make_response( json.dumps(klass().query(q=qs, terms=terms)) )

    resp.mimetype = "application/json"
    return resp

def _owner_filter():
    return {"admin.owner.exact" : current_user.id}

def _default_filter(subpaths):
    for s in subpaths:
        if s == 'journal' or s == 'article':
            return {'in_doaj':True}
    return None
