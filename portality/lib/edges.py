from urllib import parse
import json


def make_url_query(**params):
    query = make_query(**params)
    return parse.quote(json.dumps(query))


def make_query(**params):
    gsq = GeneralSearchQery(**params)
    return gsq.query()


class GeneralSearchQery(object):
    def __init__(self, terms=None):
        self.terms = terms

    def query(self):
        musts = []
        if self.terms is not None:
            musts.append(self.terms)

        return {
            "query" : {
                "filtered" : {
                    "filter" : {
                        "bool": {
                            "must": musts
                        }
                    },
                    "query" : {"match_all": {}}
                }
            }
        }