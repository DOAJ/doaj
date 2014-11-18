from portality.models import Journal
from copy import deepcopy

class AtomRecord(Journal):
    records = {
        "query" : {
            "bool" : {
                "must" : [
                    {"term" : {"admin.in_doaj" : True}},
                    # { "range" : { "last_updated" : {"gte" : "<from date>"} } }
                    { "range" : { "created_date" : {"gte" : "<from date>"} } }
                ]
            }
        },
        "size" : 20,
        # "sort" : {"last_updated" : {"order" : "desc"}}
        "sort" : {"created_date" : {"order" : "desc"}}
    }

    def list_records(self, from_date, list_size):
        q = deepcopy(self.records)
        # q["query"]["bool"]["must"][1]["range"]["last_updated"]["gte"] = from_date
        q["query"]["bool"]["must"][1]["range"]["created_date"]["gte"] = from_date
        q["size"] = list_size

        # do the query
        # print json.dumps(q)
        results = self.query(q=q)

        return [AtomRecord(**hit.get("_source")) for hit in results.get("hits", {}).get("hits", [])]
