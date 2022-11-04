# ~~EdgesIntegration:Library~~
# ~~-> Edges:Technology~~
# ~~-> Elasticsearch:Technology~~

from urllib import parse
import json


def make_url_query(**params):
    query = make_query_json(**params)
    return parse.quote_plus(query)


def make_query_json(**params):
    query = make_query(**params)
    return json.dumps(query)


def make_query(**params):
    gsq = GeneralSearchQuery(**params)
    return gsq.query()


class GeneralSearchQuery(object):
    # ~~-> Edges:Query~~
    def __init__(self, term=None, terms=None, query_string=None, sort=None):
        self.terms = None if terms is None else terms if isinstance(terms, list) else [terms]
        self.term = None if term is None else term
        self.query_string = query_string
        self.sort = sort

    def query(self):
        musts = []
        if self.terms is not None:
            for term in self.terms:
                musts.append({"terms" : term})

        if self.term is not None:
            for term in self.term:
                musts.append({"term" : term})

        if self.query_string is not None:
            qs = {"query_string": {"default_operator": "AND", "query": self.query_string}}
            musts.append(qs)

        query = {"match_all": {}}
        if len(musts) > 0:
            query = {
                "bool": {
                    "must": musts
                }
            }

        obj = {"query": query}
        if self.sort:
            if not isinstance(self.sort, list):
                obj["sort"] = [self.sort]
            else:
                obj["sort"] = self.sort

        return obj