from urllib import parse
import json


def make_url_query(**params):
    query = make_query(**params)
    return parse.quote_plus(json.dumps(query))


def make_query(**params):
    gsq = GeneralSearchQery(**params)
    return gsq.query()


class GeneralSearchQery(object):
    def __init__(self, terms=None, query_string=None):
        self.terms = None if terms is None else terms if isinstance(terms, list) else [terms]
        self.query_string = query_string

    def query(self):
        musts = []
        if self.terms is not None:
            for term in self.terms:
                musts.append({"terms" : term})

        query = {"match_all" : {}}
        if self.query_string is not None:
            query = {"query_string" : {"default_operator" : "AND", "query" : self.query_string}}

        if len(musts) > 0:
            query = {
                "bool" : {
                    "filter" : {
                        "bool": {
                            "must": musts
                        }
                    },
                    "must" : query
                }
            }

        return { "query" : query }