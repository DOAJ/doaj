import esprit
from copy import deepcopy

doaj = esprit.raw.Connection("http://doaj.org", "query", port=80)

journal_issn_query = {
    "query" : {"term" : {"_type" : "journal"}},
    "facets" : {
        "issns" : {
            "terms" : {
                "field" : "index.issn.exact",
                "size" : 30000
            }
        }
    }
}

resp = esprit.raw.search(doaj, "journal,article", journal_issn_query, method="GET")
j = resp.json()
jissns = [t.get("term") for t in j.get("facets", {}).get("issns", {}).get("terms", [])]

print("Journal ISSNs", len(jissns))

article_issn_query = {
    "query" : {"term" : {"_type" : "article"}},
    "facets" : {
        "issns" : {
            "terms" : {
                "field" : "index.issn.exact",
                "size" : 30000
            }
        }
    }
}

resp = esprit.raw.search(doaj, "journal,article", article_issn_query, method="GET")
j = resp.json()
aissns = [t.get("term") for t in j.get("facets", {}).get("issns", {}).get("terms", [])]

print("Article ISSNs", len(aissns))

missing = [issn for issn in aissns if issn not in jissns]

print("Orphaned", len(missing))
print(missing)

get_query = {
    "query" : {
        "bool" : {
            "must" : [
                {"term" : {"_type" : "article"}},
                {"term" : {"index.issn.exact" : "<issn>"}}
            ]
        }
    },
    "size" : 1
}

info = []
for m in missing:
    q = deepcopy(get_query)
    q["query"]["bool"]["must"][1]["term"]["index.issn.exact"] = m
    resp = esprit.raw.search(doaj, "journal,article", q, method="GET")
    res = esprit.raw.unpack_result(resp)
    for r in res:
        title = r.get("bibjson", {}).get("journal", {}).get("title")
        info.append((m, title))

print(info)

name_query = {
    "query" : {
        "bool" : {
            "must" : [
                {"term" : {"_type" : "journal"}},
                {"term" : {"index.title.exact" : "<title>"}}
            ]
        }
    },
    "size" : 1
}

new_info = []
unfound = []
for i, n in info:
    q = deepcopy(name_query)
    q["query"]["bool"]["must"][1]["term"]["index.title.exact"] = n
    resp = esprit.raw.search(doaj, "journal,article", q, method="GET")
    res = esprit.raw.unpack_result(resp)
    if len(res) == 0:
        unfound.append((i, n))
    for r in res:
        issns = r.get("index", {}).get("issn", [])
        new_info.append((i, n, issns))
        print(i, n, "=>", issns)

print(unfound)