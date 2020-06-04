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
        # first check the cache
        stats = Cache.get_site_statistics()
        if stats is not None:
            return stats

        # we didn't get anything from the cache, so we need to generate and
        # cache a new set

        # prep the query and result objects
        q = JournalArticleQuery()
        stats = {           # Note these values all have to be strings
            "articles" : "0",
            "journals" : "0",
            "countries" : "0",
            "searchable" : "0"
        }

        # do the query
        res = cls.query(q=q.site_statistics())

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
            stats["countries"] = locale.format("%d", len(res.get("facets", {}).get("countries", {}).get("terms", [])), grouping=True)

            # count the size of the journals facet (which tells us how many journals have articles)
            stats["searchable"] = locale.format("%d", len(res.get("facets", {}).get("journals", {}).get("terms", [])), grouping=True)

            locale.resetlocale()
        else:
            for t in terms:
                if t.get("term") == "journal":
                    stats["journals"] = "{0:,}".format(t.get("count", 0))
                if t.get("term") == "article":
                    stats["articles"] = "{0:,}".format(t.get("count", 0))

            # count the size of the countries facet
            stats["countries"] = "{0:,}".format(len(res.get("facets", {}).get("countries", {}).get("terms", [])))

            # count the size of the journals facet (which tells us how many journals have articles)
            stats["searchable"] = "{0:,}".format(len(res.get("facets", {}).get("journals", {}).get("terms", [])))

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
            }
        }
    }

    def site_statistics(self):
        return deepcopy(self.stats)