from portality import models
from portality.core import app
import esprit
import re

KEYWORDS = {
    "fields": ["id","bibjson.keywords"],
    "query": {
        "filtered": {
            "filter": {
                "exists": {"field": "index.fulltext"}
            },
            "query": {
                "match_all": {}
            }
        }
    },
    "sort": [{
        "in_doaj": "desc"
    }]
}

def rewrite_keywords_art(id):
    print("id ", id)
    article = models.Article.pull(id)
    bib = article.bibjson()
    kwords = [k.lower() for k in bib.keywords]
    bib.set_keywords(kwords)
    article.save()

def rewrite_keywords_journal(id):
    journal = models.Article.pull(id)
    bib = journal.bibjson()
    kwords = [k.lower() for k in bib.keywords]
    bib.set_keywords(kwords)
    journal.save()

if __name__ == "__main__":

    conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])

    for j in esprit.tasks.scroll(conn, models.Article.__type__, q=KEYWORDS, page_size=100, keepalive='5m'):
        if not j.has_key('bibjson.keywords'):
            continue
        keywords = j['bibjson.keywords']
        id = j['id'][0]
        print(id, keywords)

        if keywords is not None:
            for key in keywords:
                if bool(re.match(r".*[A-Z].*", key)):
                    rewrite_keywords_art(id)
                    break

    for j in esprit.tasks.scroll(conn, models.Journal.__type__, q=KEYWORDS, page_size=100, keepalive='5m'):
        keywords = j['keywords']
        id = j['id'][0]
        for key in keywords:
            if bool(re.match(r".*[A-Z].*", key)):
                rewrite_keywords_journal(id)
                break