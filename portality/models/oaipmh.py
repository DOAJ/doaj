from copy import deepcopy

from portality.models import Journal, Article, ArticleTombstone
from portality import constants


class OAIPMHRecord(object):
    earliest = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"admin.in_doaj": True}}
                ]
            }
        },
        "size": 1,
        "sort": [
            {"last_updated": {"order": "asc"}}
        ]
    }

    sets = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"admin.in_doaj": True}}
                ]
            }
        },
        "size": 0,
        "aggs": {
            "sets": {
                "terms": {
                    "field": "index.schema_subject.exact",
                    "order": {"_key": "asc"},
                    "size": 100000
                }
            }
        }
    }

    records = {
        "track_total_hits": True,
        "query": {
            "bool": {
                "must": []
            }
        },
        "from": 0,
        "size": 25
    }

    set_limit = {"term": {"index.classification.exact": "<set name>"}}
    range_limit = {"range": {"last_updated": {"gte": "<from date>", "lte": "<until date>"}}}
    created_sort = [{"last_updated": {"order": "desc"}}, {"id.exact": "desc"}]

    def earliest_datestamp(self):
        result = self.query(q=self.earliest)
        return result.get("hits", {}).get("hits", [{}])[0].get("_source", {}).get("last_updated")

    def identifier_exists(self, identifier):
        obj = self.pull(identifier)
        return obj is not None

    def list_sets(self):
        result = self.query(q=self.sets)
        sets = [t.get("key") for t in result.get("aggregations", {}).get("sets", {}).get("buckets", [])]
        return sets

    def list_records(self, from_date=None, until_date=None, oai_set=None, list_size=None, start_after=None):
        q = deepcopy(self.records)
        if start_after is not None or from_date is not None or until_date is not None or oai_set is not None:

            if oai_set is not None:
                a = oai_set.replace(constants.SUBJECTS_SCHEMA,"")
                s = deepcopy(self.set_limit)
                s["term"]["index.classification.exact"] = a
                q["query"]["bool"]["must"].append(s)

            if until_date is not None or from_date is not None or start_after is not None:
                d = deepcopy(self.range_limit)

                if start_after is not None:
                    d["range"]["last_updated"]["lte"] = start_after[0]
                elif until_date is not None:
                    d["range"]["last_updated"]["lte"] = until_date
                else:
                    del d["range"]["last_updated"]["lte"]

                if from_date is not None:
                    d["range"]["last_updated"]["gte"] = from_date
                else:
                    del d["range"]["last_updated"]["gte"]

                q["query"]["bool"]["must"].append(d)

        if list_size is not None:
            q["size"] = list_size

        if start_after is not None:
            q["from"] = start_after[1]
        else:
            q["from"] = 0

        q["sort"] = deepcopy(self.created_sort)

        # do the query
        # print json.dumps(q)

        results = self.query(q=q)

        total = results.get("hits", {}).get("total", {}).get('value', 0)
        return total, [hit.get("_source") for hit in results.get("hits", {}).get("hits", [])]


class OAIPMHArticle(OAIPMHRecord, Article):
    __type__ = "article,article_tombstone"

    def list_records(self, from_date=None, until_date=None, oai_set=None, list_size=None, start_after=None):
        total, results = super(OAIPMHArticle, self).list_records(from_date=from_date,
            until_date=until_date, oai_set=oai_set, list_size=list_size, start_after=start_after)
        return total, [Article(**r) if r.get("es_type") == "article" else ArticleTombstone(**r) for r in results]

    def pull(self, identifier):
        # override the default pull, as we must check the tombstone record too
        article = Article.pull(identifier)
        if article is None:
            article = ArticleTombstone.pull(identifier)
        return article


class OAIPMHJournal(OAIPMHRecord, Journal):
    def list_records(self, from_date=None, until_date=None, oai_set=None, list_size=None, start_after=None):
        total, results = super(OAIPMHJournal, self).list_records(from_date=from_date,
            until_date=until_date, oai_set=oai_set, list_size=list_size, start_after=start_after)
        return total, [Journal(**r) for r in results]
