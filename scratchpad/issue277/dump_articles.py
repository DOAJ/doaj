# -*- coding: utf-8 -*-

import esprit, json

def extract_bibjson(record):
    return record.get("bibjson", {})

doaj = esprit.raw.Connection("http://doaj.org", "query", port=80)

"""
Borealis (35 articles): http://doaj.org/search?source={%22query%22:{%22filtered%22:{%22query%22:{%22match_all%22:{}},%22filter%22:{%22bool%22:{%22must%22:[{%22term%22:{%22_type%22:%22article%22}},{%22term%22:{%22index.country.exact%22:%22Norway%22}},{%22term%22:{%22bibjson.journal.title.exact%22:%22Borealis%20:%20An%20International%20Journal%20of%20Hispanic%20Linguistics%22}}]}}}},%22size%22:250,%22sort%22:[{%22bibjson.year.exact%22:{%22order%22:%22asc%22}},{%22bibjson.month.exact%22:{%22order%22:%22asc%22}}]}
"""
q = {
    "query":{
        "filtered":{
            "query":{"match_all":{}},
            "filter":{
                "bool":{
                    "must":[
                        {"term":{"_type":"article"}},
                        {"term":{"index.country.exact":"Norway"}},
                        {"term":{"bibjson.journal.title.exact":"Borealis : An International Journal of Hispanic Linguistics"}}
                    ]
                }
            }
        }
    },
    "size":250,
    "sort":[
        {"bibjson.year.exact":{"order":"asc"}},
        {"bibjson.month.exact":{"order":"asc"}}
    ]
}
out = esprit.tasks.JSONListWriter("borealis.json")
esprit.tasks.dump(doaj, "journal,article", q=q, method="GET", out=out, transform=extract_bibjson)
out.close()

with open("borealis.json") as f:
    j = json.loads(f.read())
    assert len(j) == 35, len(j)

"""
NAMMCO (74 articles): http://doaj.org/search?source={%22query%22:{%22filtered%22:{%22query%22:{%22match_all%22:{}},%22filter%22:{%22bool%22:{%22must%22:[{%22term%22:{%22_type%22:%22article%22}},{%22term%22:{%22index.country.exact%22:%22Norway%22}},{%22term%22:{%22bibjson.journal.title.exact%22:%22NAMMCO%20Scientific%20Publications%22}}]}}}},%22size%22:250,%22sort%22:[{%22bibjson.year.exact%22:{%22order%22:%22asc%22}},{%22bibjson.month.exact%22:{%22order%22:%22asc%22}}]}
"""
q = {
    "query":{
        "filtered":{
            "query":{"match_all":{}},
            "filter":{
                "bool":{
                    "must":[
                        {"term":{"_type":"article"}},
                        {"term":{"index.country.exact":"Norway"}},
                        {"term":{"bibjson.journal.title.exact":"NAMMCO Scientific Publications"}}
                    ]
                }
            }
        }
    },
    "size":250,
    "sort":[
        {"bibjson.year.exact":{"order":"asc"}},
        {"bibjson.month.exact":{"order":"asc"}}
    ]
}
out = esprit.tasks.JSONListWriter("nammco.json")
esprit.tasks.dump(doaj, "journal,article", q=q, method="GET", out=out, transform=extract_bibjson)
out.close()

with open("nammco.json") as f:
    j = json.loads(f.read())
    assert len(j) == 74, len(j)

"""
Nordisk Tidsskrift (77 articles): http://doaj.org/search?source={%22query%22:{%22filtered%22:{%22query%22:{%22match_all%22:{}},%22filter%22:{%22bool%22:{%22must%22:[{%22term%22:{%22_type%22:%22article%22}},{%22term%22:{%22index.country.exact%22:%22Norway%22}},{%22term%22:{%22bibjson.journal.title.exact%22:%22Nordisk%20Tidsskrift%20for%20Helseforskning%22}}]}}}},%22size%22:250,%22sort%22:[{%22bibjson.year.exact%22:{%22order%22:%22asc%22}},{%22bibjson.month.exact%22:{%22order%22:%22asc%22}}]}
"""
q = {
    "query":{
        "filtered":{
            "query":{"match_all":{}},
            "filter":{
                "bool":{
                    "must":[
                        {"term":{"_type":"article"}},
                        {"term":{"index.country.exact":"Norway"}},
                        {"term":{"bibjson.journal.title.exact":"Nordisk Tidsskrift for Helseforskning"}}
                    ]
                }
            }
        }
    },
    "size":250,
    "sort":[
        {"bibjson.year.exact":{"order":"asc"}},
        {"bibjson.month.exact":{"order":"asc"}}
    ]
}
out = esprit.tasks.JSONListWriter("helseforskning.json")
esprit.tasks.dump(doaj, "journal,article", q=q, method="GET", out=out, transform=extract_bibjson)
out.close()

with open("helseforskning.json") as f:
    j = json.loads(f.read())
    assert len(j) == 77, len(j)

"""
Nordlit (985 articles): http://doaj.org/search?source={%22query%22:{%22filtered%22:{%22query%22:{%22match_all%22:{}},%22filter%22:{%22bool%22:{%22must%22:[{%22term%22:{%22_type%22:%22article%22}},{%22term%22:{%22index.country.exact%22:%22Norway%22}},{%22term%22:{%22bibjson.journal.title.exact%22:%22Nordlit%20:%20Tidsskrift%20i%20litteratur%20og%20kultur%20%22}}]}}}},%22size%22:250,%22sort%22:[{%22bibjson.year.exact%22:{%22order%22:%22asc%22}},{%22bibjson.month.exact%22:{%22order%22:%22asc%22}}]}
"""
q = {
    "query":{
        "filtered":{
            "query":{"match_all":{}},
            "filter":{
                "bool":{
                    "must":[
                        {"term":{"_type":"article"}},
                        {"term":{"index.country.exact":"Norway"}},
                        {"term":{"bibjson.journal.title.exact":"Nordlit : Tidsskrift i litteratur og kultur "}}
                    ]
                }
            }
        }
    },
    "size":1000,
    "sort":[
        {"bibjson.year.exact":{"order":"asc"}},
        {"bibjson.month.exact":{"order":"asc"}}
    ]
}
out = esprit.tasks.JSONListWriter("nordlit.json")
esprit.tasks.dump(doaj, "journal,article", q=q, method="GET", out=out, transform=extract_bibjson)
out.close()

with open("nordlit.json") as f:
    j = json.loads(f.read())
    assert len(j) == 985, len(j)

"""
Nordlyd (171 articles): http://doaj.org/search?source={%22query%22:{%22filtered%22:{%22query%22:{%22match_all%22:{}},%22filter%22:{%22bool%22:{%22must%22:[{%22term%22:{%22_type%22:%22article%22}},{%22term%22:{%22index.country.exact%22:%22Norway%22}},{%22term%22:{%22bibjson.journal.title.exact%22:%22Nordlyd%20:%20Troms%C3%B8%20University%20Working%20Papers%20on%20Language%20&%20Linguistics%20/%20Institutt%20for%20Spr%C3%A5k%20og%20Litteratur,%20Universitetet%20i%20Troms%C3%B8%22}}]}}}},%22size%22:250,%22sort%22:[{%22bibjson.year.exact%22:{%22order%22:%22asc%22}},{%22bibjson.month.exact%22:{%22order%22:%22asc%22}}]}
"""

q = {
    "query":{
        "filtered":{
            "query":{"match_all":{}},
            "filter":{
                "bool":{
                    "must":[
                        {"term":{"_type":"article"}},
                        {"term":{"index.country.exact":"Norway"}},
                        {"term":{"bibjson.journal.title.exact":"Nordlyd : Tromsø University Working Papers on Language & Linguistics / Institutt for Språk og Litteratur, Universitetet i Tromsø"}}
                    ]
                }
            }
        }
    },
    "size":250,
    "sort":[
        {"bibjson.year.exact":{"order":"asc"}},
        {"bibjson.month.exact":{"order":"asc"}}
    ]
}
out = esprit.tasks.JSONListWriter("nordlyd.json")
esprit.tasks.dump(doaj, "journal,article", q=q, method="GET", out=out, transform=extract_bibjson)
out.close()

with open("nordlyd.json") as f:
    j = json.loads(f.read())
    assert len(j) == 171, len(j)

"""
Poljarnyj (102 articles): http://doaj.org/search?source={%22query%22:{%22filtered%22:{%22query%22:{%22match_all%22:{}},%22filter%22:{%22bool%22:{%22must%22:[{%22term%22:{%22_type%22:%22article%22}},{%22term%22:{%22index.country.exact%22:%22Norway%22}},{%22term%22:{%22bibjson.journal.title.exact%22:%22Poljarnyj%20Vestnik%22}}]}}}},%22size%22:250,%22sort%22:[{%22bibjson.year.exact%22:{%22order%22:%22asc%22}},{%22bibjson.month.exact%22:{%22order%22:%22asc%22}}]}
"""

q = {
    "query":{
        "filtered":{
            "query":{"match_all":{}},
            "filter":{
                "bool":{
                    "must":[
                        {"term":{"_type":"article"}},
                        {"term":{"index.country.exact":"Norway"}},
                        {"term":{"bibjson.journal.title.exact":"Poljarnyj Vestnik"}}
                    ]
                }
            }
        }
    },
    "size":250,
    "sort":[
        {"bibjson.year.exact":{"order":"asc"}},
        {"bibjson.month.exact":{"order":"asc"}}
    ]
}
out = esprit.tasks.JSONListWriter("poljarnyj.json")
esprit.tasks.dump(doaj, "journal,article", q=q, method="GET", out=out, transform=extract_bibjson)
out.close()

with open("poljarnyj.json") as f:
    j = json.loads(f.read())
    assert len(j) == 102, len(j)

"""
Rangifer (2626 articles): http://doaj.org/search?source={%22query%22:{%22filtered%22:{%22query%22:{%22match_all%22:{}},%22filter%22:{%22bool%22:{%22must%22:[{%22term%22:{%22_type%22:%22article%22}},{%22term%22:{%22index.country.exact%22:%22Norway%22}},{%22term%22:{%22bibjson.journal.title.exact%22:%22Rangifer%22}}]}}}},%22size%22:250,%22sort%22:[{%22bibjson.year.exact%22:{%22order%22:%22asc%22}},{%22bibjson.month.exact%22:{%22order%22:%22asc%22}}]}
"""

q = {
    "query":{
        "filtered":{
            "query":{"match_all":{}},
            "filter":{
                "bool":{
                    "must":[
                        {"term":{"_type":"article"}},
                        {"term":{"index.country.exact":"Norway"}},
                        {"term":{"bibjson.journal.title.exact":"Rangifer"}}
                    ]
                }
            }
        }
    },
    "sort":[
        {"bibjson.year.exact":{"order":"asc"}},
        {"bibjson.month.exact":{"order":"asc"}}
    ]
}

out = esprit.tasks.JSONListWriter("rangifer.json")
esprit.tasks.dump(doaj, "journal,article", q=q, method="GET", out=out, transform=extract_bibjson)
out.close()

with open("rangifer.json") as f:
    j = json.loads(f.read())
    assert len(j) == 2626, len(j)