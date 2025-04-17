from portality.core import app, es_connection
from portality.util import ipt_prefix
from portality.bll import exceptions
from portality.lib import plugin
from copy import deepcopy

class QueryService(object):
    """
    ~~Query:Service~~
    """
    def _get_config_for_search(self, domain, index_type, account):
        # load the query route config and the path we are being requested for
        # ~~-> Query:Config~~
        qrs = app.config.get("QUERY_ROUTE", {})

        # get the configuration for this url route
        route_cfg = None
        for key in qrs:
            if domain == key:
                route_cfg = qrs.get(key)
                break

        if route_cfg is None:
            raise exceptions.AuthoriseException(exceptions.AuthoriseException.NOT_AUTHORISED)

        cfg = route_cfg.get(index_type)
        if cfg is None:
            raise exceptions.AuthoriseException(exceptions.AuthoriseException.NOT_AUTHORISED)

        # does the user have to be authenticated
        if cfg.get("auth", True):
            if account is None:
                raise exceptions.AuthoriseException(exceptions.AuthoriseException.NOT_AUTHORISED)

            # if so, does the user require a role
            role = cfg.get("role")
            if role is not None and not account.has_role(role):
                raise exceptions.AuthoriseException(exceptions.AuthoriseException.WRONG_ROLE)

        return cfg

    def _validate_query(self, cfg, query):
        validators = cfg.get("query_validators")
        if validators:
            for validator in validators:
                filters = app.config.get("QUERY_FILTERS", {})
                validator_path = filters.get(validator)
                fn = plugin.load_function(validator_path)
                if fn is None:
                    msg = "Unable to load query validator for {x}".format(x=validator)
                    raise exceptions.ConfigurationException(msg)

                if not fn(query):
                    return False
        return True


    def _pre_filter_search_query(self, cfg, query):
        # now run the query through the filters
        filters = app.config.get("QUERY_FILTERS", {})
        filter_names = cfg.get("query_filters", [])
        for filter_name in filter_names:
            # because of back-compat, we have to do a few tricky things here...
            # filter may be the name of a filter in the list of query filters
            fn = plugin.load_function(filters.get(filter_name))
            if fn is None:
                msg = "Unable to load query filter for {x}".format(x=filter_name)
                raise exceptions.ConfigurationException(msg)

            # run the filter
            fn(query)

        return query

    def _post_filter_search_results(self, cfg, res, unpacked=False):
        filters = app.config.get("QUERY_FILTERS", {})
        result_filter_names = cfg.get("result_filters", [])
        for result_filter_name in result_filter_names:
            fn = plugin.load_function(filters.get(result_filter_name))
            if fn is None:
                msg = "Unable to load result filter for {x}".format(x=result_filter_name)
                raise exceptions.ConfigurationException(msg)

            # apply the result filter
            res = fn(res, unpacked=unpacked)

        return res

    def _get_query(self, cfg, raw_query):
        query = Query()
        if raw_query is not None:
            query = Query(raw_query)

        # validate the query, to make sure it is of a permitted form
        if not self._validate_query(cfg, query):
            raise exceptions.AuthoriseException()

        # add any required filters to the query
        query = self._pre_filter_search_query(cfg, query)
        return query

    def _get_dao_klass(self, cfg):
        # get the name of the model that will handle this query, and then look up
        # the class that will handle it
        dao_name = cfg.get("dao")
        dao_klass = plugin.load_class(dao_name)
        if dao_klass is None:
            raise exceptions.NoSuchObjectException(dao_name)
        return dao_klass

    def search(self, domain, index_type, raw_query, account, additional_parameters):
        cfg = self._get_config_for_search(domain, index_type, account)

        # check that the request values permit a query to this endpoint
        required_parameters = cfg.get("required_parameters")
        if required_parameters is not None:
            for k, vs in required_parameters.items():
                val = additional_parameters.get(k)
                if val is None or val not in vs:
                    raise exceptions.AuthoriseException()

        dao_klass = self._get_dao_klass(cfg)

        # get the query
        query = self._get_query(cfg, raw_query)

        # send the query
        res = dao_klass.query(q=query.as_dict())

        # filter the results as needed
        res = self._post_filter_search_results(cfg, res)

        return res

    def scroll(self, domain, index_type, raw_query, account, page_size, scan=False):
        cfg = self._get_config_for_search(domain, index_type, account)

        dao_klass = self._get_dao_klass(cfg)

        # get the query
        query = self._get_query(cfg, raw_query)

        # get the scroll parameters
        if page_size is None:
            page_size = cfg.get("page_size", 1000)
        limit = cfg.get("limit", None)
        keepalive = cfg.get("keepalive", "1m")

        # ~~->Elasticsearch:Technology~~
        for result in dao_klass.iterate(q=query.as_dict(), page_size=page_size, limit=limit, wrap=False, keepalive=keepalive):
            res = self._post_filter_search_results(cfg, result, unpacked=True)
            yield res

    def make_actionable_query(self, domain, index_type, account, raw_query):
        cfg = self._get_config_for_search(domain, index_type, account)
        query = self._get_query(cfg, raw_query)
        return query

class Query(object):
    """
    ~~Query:Query -> Elasticsearch:Technology~~
    """
    def __init__(self, raw=None, filtered=False):
        self.q = {"track_total_hits" : True, "query": {"match_all": {}}} if raw is None else raw
        self.filtered = filtered is True or self.q.get("query", {}).get("filtered") is not None
        if self.filtered:
            # FIXME: this is just to help us catch filtered queries during development.  Once we have them
            # all, all the filtering logic in this class can come out
            raise Exception("Filtered queries are no longer supported")

    def convert_to_bool(self):
        if self.filtered is True:
            return

        current_query = None
        if "query" in self.q:
            if "bool" in self.q["query"]:
                return
            current_query = deepcopy(self.q["query"])
            del self.q["query"]
            if len(list(current_query.keys())) == 0:
                current_query = None

        if "query" not in self.q:
            self.q["query"] = {}
        if "bool" not in self.q["query"]:
            self.q["query"]["bool"] = {}

        if current_query is not None:
            if "must" not in self.q["query"]["bool"]:
                self.q["query"]["bool"]["must"] = []

            self.q["query"]["bool"]["must"].append(current_query)

    def add_must(self, filter):
        # self.convert_to_filtered()
        self.convert_to_bool()
        context = self.q["query"]["bool"]
        if "must" not in context:
            context["must"] = []
        context["must"].append(filter)

    def get_field_context(self):
        """Get query string context"""
        context = None
        if "query_string" in self.q["query"]:
            context = self.q["query"]["query_string"]

        elif "bool" in self.q["query"]:
            if "must" in self.q["query"]["bool"]:
                context = self.q["query"]["bool"]["must"]
        return context

    def add_default_field(self, value: str):
        """ Add a default field to the query string, if one is not already present"""
        context = self.get_field_context()

        if context:
            if isinstance(context, dict):
                if "default_field" not in context:
                    context["default_field"] = value
            elif isinstance(context, list):
                for item in context:
                    if "query_string" in item:
                        if "default_field" not in item["query_string"]:
                            item["query_string"]["default_field"] = value
                            break

    def add_should(self, filter, minimum_should_match=1):
        self.convert_to_bool()
        context = self.q["query"]["bool"]
        if "should" not in context:
            context["should"] = []
        if isinstance(filter, list):
            context["should"].extend(filter)
        else:
            context["should"].append(filter)
        context["minimum_should_match"] = minimum_should_match

    def add_must_filter(self, filter):
        self.convert_to_bool()
        context = self.q["query"]["bool"]
        if "filter" not in context:
            context["filter"] = []

        context["filter"].append(filter)

    def add_must_not(self, filter):
        self.convert_to_bool()
        context = self.q["query"]["bool"]
        if "must_not" not in context:
            context["must_not"] = []

        context["must_not"].append(filter)

    def clear_match_all(self):
        if "match_all" in self.q["query"]:
            del self.q["query"]["match_all"]

    def has_facets(self):
        return "facets" in self.q or "aggregations" in self.q or "aggs" in self.q

    def clear_facets(self):
        if "facets" in self.q:
            del self.q["facets"]
        if "aggregations" in self.q:
            del self.q["aggregations"]
        if "aggs" in self.q:
            del self.q["aggs"]

    def size(self):
        if "size" in self.q:
            try:
                return int(self.q["size"])
            except ValueError:
                app.logger.warn("Invalid size parameter in query: [{x}], "
                                "expected integer value".format(x=self.q["size"]))
        return 10

    def from_result(self):
        if "from" in self.q:
            try:
                return int(self.q["from"])
            except ValueError:
                app.logger.warn("Invalid from parameter in query: [{x}], "
                                "expected integer value".format(x=self.q["from"]))
        return 0

    def as_dict(self):
        return self.q

    def add_include(self, fields):
        if "_source" not in self.q:
            self.q["_source"] = {}
        if "includes" not in self.q["_source"]:
            self.q["_source"]["includes"] = []
        if not isinstance(fields, list):
            fields = [fields]
        self.q["_source"]["includes"] = list(set(self.q["_source"]["includes"] + fields))

    def sort(self):
        return self.q.get("sort")

    def set_sort(self, s):
        self.q["sort"] = s


class QueryFilterException(Exception):
    pass
