# -*- coding: utf-8 -*-

from portality import models

# search on "BiD : Textos Universitaris de Biblioteconomia i Documentació" for user 15755886
query = {
    "query":{
        "filtered":{
            "query":{
                "query_string":{
                    "query":"BiD \\: Textos Universitaris de Biblioteconomia i Documentació",
                    "default_operator":"AND"
                }
            },
            "filter":{
                "bool":{
                    "must":[
                        {"term":{"_type":"article"}}
                    ]
                }
            }
        }
    }
}
models.Article.delete_selected(query=query)

# everything from user 14385627
models.Article.delete_selected(owner="14385627")

# everything from user 20007558
models.Article.delete_selected(owner="20007558")

# everything from user 16772954 between 2002 and 2008 (inclusive)
# (that's issn 1677-2954, FYI)
issns = models.Journal.issns_by_owner("16772954")
query = {
    "query" : {
        "bool" : {
            "must" : [
                { "terms" : {"index.issn.exact" : issns} },
                { "terms" : {"bibjson.year.exact" : ["2002", "2003", "2004", "2005", "2006", "2007", "2008"]} }
            ]
        }
    }
}
models.Article.delete_selected(query=query)

# delete all articles from account 21106126
# BUT do not delete Vol 6, Synergie d'Espagne: https://doaj.org/toc/62eb7104aed2402389560bc1a3f40fba/6
# or ANY articles from Synergies de Canada: https://doaj.org/toc/53ed46ecc01e4404acef946d75adb9e8

# get all the issns for this owner, then remove the special cases
issns = models.Journal.issns_by_owner("21106126")

# Synergies de Canada = 1920-4051
if "1920-4051" in issns:
    del issns[issns.index("1920-4051")]

# Synergie d'Espagne = 1961-9359
if "1961-9359" in issns:
    del issns[issns.index("1961-9359")]

query = models.ArticleQuery(issns=issns)
models.Article.delete_selected(query=query.query())

# now do a specific request on the volumes other than 6 for 1961-9359
volumes = models.Article.list_volumes(["1961-9359"])
if "6" in volumes:
    del volumes[volumes.index("6")]
query = {
    "query" : {
        "bool" : {
            "must" : [
                { "terms" : {"index.issn.exact" : ["1961-9359"]} },
                { "terms" : {"bibjson.journal.volume.exact" : volumes} }
            ]
        }
    }
}
models.Article.delete_selected(query=query)
