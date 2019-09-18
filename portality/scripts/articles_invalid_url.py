from portality import models
from portality.core import app
from portality.clcsv import UnicodeWriter
import esprit
import codecs
import re

INVALID_URLS = {
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

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    args = parser.parse_args()

    if not args.out:
        print "Please specify an output file path with the -o option"
        parser.print_help()
        exit()

    conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])

    with codecs.open(args.out, "wb", "utf-8") as f:
        writer = UnicodeWriter(f)
        writer.writerow(["ID", "Journal Name", "URL", "In Doaj", "Created Date"])

        for j in esprit.tasks.scroll(conn, models.Article.__type__, q=INVALID_URLS, page_size=100, keepalive='5m'):
            article = models.Article(_source=j)
            bibjson = article.bibjson()
            fulltext = bibjson.get_single_url("fulltext")

            if (fulltext is not None) and not bool(re.match(r"^https?://([^/:]+\.[a-zA-Z]{2,10}|([0-9]{1,3}\.){3}[0-9]{1,3})(:[0-9]+)?(/.*)?$",fulltext)):
                writer.writerow([article.id, bibjson.title, bibjson.get_single_url("fulltext"), article.is_in_doaj()])