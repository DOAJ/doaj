from portality.dao import DomainObject
from portality.models.cache import Cache
from portality.models import Journal, Article


class JournalArticle(DomainObject):
    __type__ = 'journal,article'
    __readonly__ = True  # TODO actually heed this attribute in all DomainObject methods which modify data

    @classmethod
    def site_statistics(cls):

        stats = Cache.get_site_statistics()
        if stats is not None:
            return stats

        # we didn't get anything from the cache, so we need to generate and
        # cache a new set

        # prep the query and result objects
        stats = {           # Note these values all have to be strings
            "journals" : "0",
            "countries" : "0",
            "abstracts" : "0",
            "new_journals" : "0",
            "no_apc" : "0"
        }

        # get the journal data
        q = JournalStatsQuery()
        journal_data = Journal.query(q=q.stats)

        stats["journals"] = "{0:,}".format(journal_data.get("hits", {}).get("total", {}).get('value', 0))
        stats["countries"] = "{0:,}".format(len(journal_data.get("aggregations", {}).get("countries", {}).get("buckets", [])))

        apc_buckets = journal_data.get("aggregations", {}).get("apcs", {}).get("buckets", [])
        for b in apc_buckets:
            if b.get("key") == "No":
                stats["no_apc"] = "{0:,}".format(b.get("doc_count"))
                break

        nj_stat = journal_data.get("aggregations", {}).get("creation", {}).get("buckets", [])
        if len(nj_stat) > 0:
            stats["new_journals"] = "{0:,}".format(nj_stat[0].get("doc_count", 0))

        # get the article data
        qa = ArticleStatsQuery()
        article_data = Article.query(q=qa.q)
        stats["abstracts"] = "{0:,}".format(article_data.get("hits", {}).get("total", {}).get('value', 0))

        # now cache and return
        Cache.cache_site_statistics(stats)

        return stats


class JournalStatsQuery(object):
    stats = {
        "track_total_hits" : True,
        "query": {
            "bool": {
                "must": [
                    {"term": {"admin.in_doaj": True}}
                ]
            }
        },
        "size": 0,
        "aggs": {
            "countries" : {
            	"terms" : {"field" : "index.country.exact", "size" : 500}
            },
            "apcs" : {
                "terms" : {"field" : "index.has_apc.exact"}
            },
            "creation" : {
                "date_range" : {
                    "field" : "created_date",
                    "ranges" : [
                        {"from" : "now-1M"}
                    ]
                }
            }
        }
    }


class ArticleStatsQuery(object):
    q = {
        "track_total_hits" : True,
        "query": {
            "bool": {
                "must": {"term": {"admin.in_doaj": "true"}}
            }
        },
        "size": 0
    }
