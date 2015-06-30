from portality.api.v1.common import Api
from portality import models
from portality.core import app
from datetime import datetime
import esprit
import re, json

class DiscoveryException(Exception):
    pass

class SearchResult(object):
    def __init__(self, raw=None):
        self.data = raw if raw is not None else {}

def substitute(query, substitutions):
    if len(substitutions.keys()) == 0:
        return query

    # apply the regex escapes to the substitutions, so we know they
    # are ready to be matched
    escsubs = {}
    for k, v in substitutions.iteritems():
        escsubs[k.replace(":", "\\:")] = v

    # define a function which takes the match group and returns the
    # substitution if there is one
    def rep(match):
        for k, v in escsubs.iteritems():
            if k == match.group(1):
                return v
        return match.group(1)

    # define the regular expressions for splitting and then extracting
    # the field to be substituted
    split_rx = "([^\\\\]:)"
    field_rx = "([^\s\+\-\(\)\"]+?):$"

    # split the query around any unescaped colons
    bits = re.split(split_rx, query)

    # stitch back together the split sections and the separators
    segs = [bits[i] + bits[i+1] for i in range(0, len(bits), 2) if i+1 < len(bits)] + [bits[len(bits) - 1]] if len(bits) % 2 == 1 else []

    # substitute the fields as required
    subs = []
    for seg in segs:
        if seg.endswith(":"):
            subs.append(re.sub(field_rx, rep, seg))
        else:
            subs.append(seg)

    return ":".join(subs)

def allowed(query, wildcards=False, fuzzy=False):
    if not wildcards:
        rx = "(.+[^\\\\][\?\*]+.*)"
        if re.search(rx, query):
            return False

    if not fuzzy:
        # this covers both fuzzy searching and proximity searching
        rx = "(.+[^\\\\]~[0-9]{0,1}[\.]{0,1}[0-9]{0,1})"
        if re.search(rx, query):
            return False

    return True


class DiscoveryApi(Api):

    @classmethod
    def _make_query(cls, q, page, page_size, subs):
        if not allowed(q):
            raise DiscoveryException("Query contains disallowed Lucene features")

        q = substitute(q, subs)
        # print q

        # calculate the position of the from cursor in the document set
        fro = (page - 1) * page_size

        # assemble the query
        query = SearchQuery(q, fro, page_size)
        # print json.dumps(query.query())

        return query

    @classmethod
    def _make_response(cls, res, q, page, page_size, obs):
        total = res.get("hits", {}).get("total", 0)

        # build the response object
        result = {
            "total" : total,
            "page" : page,
            "pageSize" : page_size,
            "timestamp" : datetime.utcnow().strftime("%Y-%m%dT%H:%M:%SZ"),
            "query" : q,
            "results" : obs
        }

        return SearchResult(result)

    @classmethod
    def search_articles(cls, q, page, page_size):
        subs = app.config.get("DISCOVERY_ARTICLE_SUBS", {})
        query = cls._make_query(q, page, page_size, subs)

        # execute the query against the articles
        res = models.Article.query(q=query.query(), consistent_order=False)

        # check to see if there was a search error
        if res.get("error") is not None:
            app.logger.error("Error executing discovery query search: {x}".format(x=res.get("error")))
            raise DiscoveryException("There was an error executing your query")

        obs = [models.Article(**raw) for raw in esprit.raw.unpack_json_result(res)]
        return cls._make_response(res, q, page, page_size, obs)

    @classmethod
    def search_journals(cls, q, page, page_size):
        subs = app.config.get("DISCOVERY_JOURNAL_SUBS", {})
        query = cls._make_query(q, page, page_size, subs)

        # execute the query against the articles
        res = models.Journal.query(q=query.query(), consistent_order=False)

        # check to see if there was a search error
        if res.get("error") is not None:
            app.logger.error("Error executing discovery query search: {x}".format(x=res.get("error")))
            raise DiscoveryException("There was an error executing your query")

        obs = [models.Journal(**raw) for raw in esprit.raw.unpack_json_result(res)]
        return cls._make_response(res, q, page, page_size, obs)

class SearchQuery(object):
    def __init__(self, qs, fro, psize):
        self.qs = qs
        self.fro = fro
        self.psize = psize

    def query(self):
        return {
            "query" : {
                "filtered" : {
                    "filter" : {
                        "bool" : {
                            "must" : [
                                {"term" : {"admin.in_doaj": True}}
                            ]
                        }
                    },
                    "query" : {
                        "query_string" : {
                            "query" : self.qs
                        }
                    }
                }
            },
            "_source": {
                "include": ["last_updated", "created_date", "id", "bibjson"],
                "exclude": [],
            },
            "from" : self.fro,
            "size" : self.psize
        }