import json, urllib2
# from esprit.models import Query

from flask import Blueprint, request, abort, make_response
from flask.ext.login import current_user

from portality.core import app
from portality.lib import plugin
from portality import util

blueprint = Blueprint('query', __name__)

class QueryFilterException(Exception):
    pass

# pass queries direct to index. POST only for receipt of complex query objects
@blueprint.route('/<path:path>', methods=['GET','POST'])
@util.jsonp
def query(path=None):
    # get the bits out of the path, and ensure that we have at least some parts to work with
    pathparts = path.strip('/').split('/')
    if len(pathparts) == 0:
        abort(400)

    # load the query route config and the path we are being requested for
    qrs = app.config.get("QUERY_ROUTE", {})
    frag = request.path

    # get the configuration for this url route
    route_cfg = None
    for key in qrs:
        if frag.startswith("/" + key):
            route_cfg = qrs.get(key)
            break

    # if no route cfg is found this is not authorised
    if route_cfg is None:
        abort(401)

    # get the configuration for the specific index being queried
    index = pathparts[0]
    cfg = route_cfg.get(index)
    if cfg is None:
        abort(401)

    # does the user have to be authenticated
    if cfg.get("auth"):
        if current_user is None or current_user.is_anonymous():
            abort(401)

        # if so, does the user require a role
        role = cfg.get("roles")
        if role is not None and not current_user.has_role(role):
            abort(401)

    # get the name of the model that will handle this query, and then look up
    # the class that will handle it
    dao_name = cfg.get("dao")
    dao_klass = plugin.load_class(dao_name)
    if dao_klass is None:
        abort(404)

    # now work out what kind of operation is being asked for
    # if _search is specified, then this is a normal query
    search = False
    by_id = None
    if len(pathparts) == 1 or (len(pathparts) == 2 and pathparts[1] == "_search"):
        search = True
    elif len(pathparts) == 2:
        if request.method == "POST":
            abort(401)
        by_id = pathparts[1]
    else:
        abort(400)

    resp = None
    if by_id is not None:
        rec = dao_klass.pull(by_id, wrap=False)
        resp = make_response(rec)
    elif search:
        q = Query()

        # if this is a POST, read the contents out of the body
        if request.method == "POST":
            q = Query(request.json) if request.json else Query(dict(request.form).keys()[-1]) # FIXME: does this actually work?

        # if there is a q param, make it into a query string query
        #elif 'q' in request.values:
        #    s = request.values['q']
        #    op = request.values.get('default_operator')
        #    q.query_string(s, op)

        # if there is a source param, load the json from it
        elif 'source' in request.values:
            q = Query(json.loads(urllib2.unquote(request.values['source'])))

        # now run the query through the filters
        filters = app.config.get("QUERY_FILTERS", {})
        filter_names = cfg.get("query_filters", [])
        for filter_name in filter_names:
            # because of back-compat, we have to do a few tricky things here...
            # filter may be the name of a filter in the list of query filters
            fn = plugin.load_function(filters.get(filter_name))
            if fn is None:
                app.logger.info("Unable to load query filter for {x}".format(x=filter_name))
                abort(500)

            try:
                fn(q)
            except QueryFilterException as e:
                abort(400)
            except:
                abort(500)

        # send the query
        res = dao_klass.query(q=q.as_dict())

        result_filter_names = cfg.get("result_filters", [])
        for result_filter_name in result_filter_names:
            fn = plugin.load_function(filters.get(result_filter_name))
            if fn is None:
                app.logger.info("Unable to load result filter for {x}".format(x=result_filter_name))
                abort(500)

            # apply the result filter
            res = fn(res)

        resp = make_response(json.dumps(res))
    else:
        abort(400)

    resp.mimetype = "application/json"
    return resp


class Query(object):
    def __init__(self, raw=None, filtered=False):
        self.q = {"query": {"match_all": {}}} if raw is None else raw
        self.filtered = filtered is True or self.q.get("query", {}).get("filtered") is not None

    def ensure_filtered(self):
        if "query" not in self.q:
            self.q["query"] = {}
        if "filtered" not in self.q["query"]:
            self.q["query"]["filtered"] = {}
        if "filter" not in self.q["query"]["filtered"]:
            self.q["query"]["filtered"]["filter"] = {}

    def add_must(self, filter):
        context = self.q["query"]
        if self.filtered:
            self.ensure_filtered()
            context = self.q["query"]["filtered"]["filter"]

        if "bool" not in context:
            context["bool"] = {}
        if "must" not in context["bool"]:
            context["bool"]["must"] = []

        context["bool"]["must"].append(filter)

    def clear_match_all(self):
        if "match_all" in self.q["query"]:
            del self.q["query"]["match_all"]

    def as_dict(self):
        return self.q

"""
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
    editor_filter = False # don't apply the editor group filter unless expressly requested
    reapp_filter = False # don't apply the reapplication status filter unless expressly requested
    associate_filter = False # don't limit to associates unless expressly requested
    public_result_filter = False
    role = None
    qr = app.config.get("QUERY_ROUTE", {})
    frag = request.path
    for qroute in qr:
        if frag.startswith("/" + qroute):
            default_filter = qr[qroute].get("default_filter", True)
            role = qr[qroute].get("role")
            owner_filter = qr[qroute].get("owner_filter")
            editor_filter = qr[qroute].get("editor_filter", False)
            associate_filter = qr[qroute].get("associate_filter", False)
            reapp_filter = qr[qroute].get("reapp_filter", False)
            public_result_filter = qr[qroute].get("public_result_filter", False)
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
            if 'default_operator' in request.values:
                qs['query']['query_string']['default_operator'] = request.values['default_operator']
        elif 'source' in request.values:
            unquoted_source = urllib2.unquote(request.values['source'])
            try:
                qs = json.loads(unquoted_source)
            except ValueError:
                app.logger.exception("Problematic query:\n    {0}\n".format(unquoted_source))
        else: 
            qs = {'query': {'match_all': {}}}

        for item in request.values:
            if item not in ['q','source','callback','_', 'default_operator'] and isinstance(qs,dict):
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


        terms = {}
        shoulds = {}
        if default_filter:
            terms.update(_default_filter(subpaths))
        
        if owner_filter:
            terms.update(_owner_filter())

        if editor_filter:
            shoulds.update(_editor_filter())

        if reapp_filter:
            shoulds.update(_update_request_filter())

        if associate_filter:
            terms.update(_associate_filter())

        results = klass().query(q=qs, terms=terms, should_terms=shoulds)
        if public_result_filter:
            results = _result_filter(results)
        resp = make_response( json.dumps(results) )

    resp.mimetype = "application/json"
    return resp

def _associate_filter():
    return {"admin.editor.exact" : current_user.id}

def _editor_filter():
    '''
    Apply filter to include only items assigned to editor groups that the current user is the editor for
    '''
    gnames = []
    groups = models.EditorGroup.groups_by_editor(current_user.id)
    for g in groups:
        gnames.append(g.name)
    return {"admin.editor_group.exact" : gnames}

def _update_request_filter():
    return {"created_date" : ["update_request", "submitted"]}

def _owner_filter():
    return {"admin.owner.exact" : current_user.id}

def _default_filter(subpaths):
    for s in subpaths:
        if s == 'journal' or s == 'article':
            return {'in_doaj':True}
    return None

def _result_filter(results):
    if "hits" not in results:
        return results
    if "hits" not in results["hits"]:
        return results

    for hit in results["hits"]["hits"]:
        if "_source" in hit:
            if "admin" in hit["_source"]:
                for k in hit["_source"]["admin"].keys():
                    if k not in ["ticked", "seal"]:
                        del hit["_source"]["admin"][k]

    return results
"""