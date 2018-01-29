import json, urllib2
# from esprit.models import Query

from flask import Blueprint, request, abort, make_response
from flask.ext.login import current_user

from portality.core import app
from portality.lib import plugin
from portality import util

from copy import deepcopy

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

    def convert_to_filtered(self):
        if self.filtered is True:
            return

        current_query = None
        if "query" in self.q:
            current_query = deepcopy(self.q["query"])
            del self.q["query"]
            if len(current_query.keys()) == 0:
                current_query = None

        self.filtered = True
        if "query" not in self.q:
            self.q["query"] = {}
        if "filtered" not in self.q["query"]:
            self.q["query"]["filtered"] = {}
        if "filter" not in self.q["query"]["filtered"]:
            self.q["query"]["filtered"]["filter"] = {}

        if "query" not in self.q["query"]["filtered"] and current_query is not None:
            self.q["query"]["filtered"]["query"] = current_query

    def add_must(self, filter):
        self.convert_to_filtered()
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

