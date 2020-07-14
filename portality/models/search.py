from portality.dao import DomainObject
from portality.models.cache import Cache
import sys
import locale
from copy import deepcopy

class JournalArticle(DomainObject):
    __type__ = 'journal,article'
    __readonly__ = True  # TODO actually heed this attribute in all DomainObject methods which modify data

    @classmethod
    def site_statistics(cls):
        # TODO: remove cache below to actully use it
        # stats = Cache.get_site_statistics()
        # if stats is not None:
        #     return stats

        # we didn't get anything from the cache, so we need to generate and
        # cache a new set

        # prep the query and result objects
        q = JournalArticleQuery()
        stats = {           # Note these values all have to be strings
            "journals" : "0",
            "countries" : "0",
            "abstracts" : "0",
            "last_updated" : "0",
            "no_apc" : "0"
        }

        # do the query
        res = cls.query(q=q.site_statistics())
        res2 = cls.query(q=q.site_statistics(looked_for="last_updated"))
        res3 = cls.query(q=q.site_statistics(looked_for="no_apc"))

        # pull the journal and article facets out
        terms = res.get("facets", {}).get("type", {}).get("terms", [])


        # can't use the Python , option when formatting numbers since we
        # need to be compatible with Python 2.6
        # otherwise we would be able to do "{0:,}".format(t.get("count", 0))

        if sys.version_info[0] == 2 and sys.version_info[1] < 7:
            locale.setlocale(locale.LC_ALL, 'en_US')
            for t in terms:
                if t.get("term") == "journal":
                    stats["journals"] = locale.format("%d", t.get("count", 0), grouping=True)
                if t.get("term") == "article":
                    stats["articles"] = locale.format("%d", t.get("count", 0), grouping=True)

            # count the size of the countries facet
            stats["countries"] = locale.format("%d", len(res.get("facets", {}).get("countries", {}).get("terms", [])),
                                               grouping=True)
            stats["abstracts"] = locale.format("%d", len(res.get("facets", {}).get("abstracts", {}).get("terms", [])),
                                               grouping=True)
            stats["last_updated"] = locale.format("%d", len(res2.get("hits", {})))
            stats["no_apc"] = locale.format("%d", len(res3.get("hits", {})))

            locale.resetlocale()
        else:
            for t in terms:
                if t.get("term") == "journal":
                    stats["journals"] = "{0:,}".format(t.get("count", 0))
                if t.get("term") == "article":
                    stats["articles"] = "{0:,}".format(t.get("count", 0))

            # count the size of the countries facet
            stats["countries"] = "{0:,}".format(len(res.get("facets", {}).get("countries", {}).get("terms", [])))

            # count the size of article abstract's
            stats["abstracts"] = "{0:,}".format(len(res.get("facets", {}).get("abstracts", {}).get("terms", [])))
            stats["last_updated"] = "{0:,}".format(len(res2.get("hits", {}).get("hits", [])))
            stats["no_apc"] = "{0:,}".format(len(res3.get("hits", {}).get("hits", [])))

        # now cache and return
        Cache.cache_site_statistics(stats)

        return stats


class JournalArticleQuery(object):
    stats = {
        "query":{
            "bool" : {
                "must" : [
                    {"term" : {"admin.in_doaj" : True}}
                ]
            }
        },
        "size" : 0,
        "facets" : {
            "type" : {
                "terms": {"field": "es_type"}
            },
            "countries" : {
                "terms" : {"field" : "index.country.exact", "size" : 10000 }
            },
            "journals" : {
                "terms" : {"field" : "bibjson.journal.title.exact", "size" : 15000 }
            },
            "abstracts" : {
                "terms" : {"field" : "bibjson.abstract.exact", "size" : 10000000}
            }
        }
    }

    last_updated_stats = {
        "query": {
            "filtered" : {
                "query" : {
                    "term": {"in_doaj" : True}
                },
                "filter": {
                    "range": {
                        "last_manual_update": {
                            "gte": "now-25y",   # TODO: change to the correct value
                            "lt": "now"
                        }
                    }
                }
            }
        }
    }
    # TODO: look for journals only
    no_apc = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"bibsjon.apc.has_apc": True}},        # TODO: check if looks for journals only
                    {"term": {"in_doaj": True}}
                ]
            }
        }
    }

    def site_statistics(self, looked_for=None):
        if looked_for == "last_updated":
            return deepcopy(self.last_updated_stats)
        if looked_for == "no_apc":
            return deepcopy(self.no_apc)
        return deepcopy(self.stats)
