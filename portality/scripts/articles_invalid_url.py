from portality import models
from portality.util import ipt_prefix
import re
import csv

INVALID_URLS = {
    "query": {
        "bool": {
            "filter": {
                "exists": {"field": "index.fulltext"}
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
        print("Please specify an output file path with the -o option")
        parser.print_help()
        exit()

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Article Title", "URL", "In Doaj", "Created Date"])

        for article in Article.scroll(q=INVALID_URLS, page_size=100, keepalive='5m'):
            bibjson = article.bibjson()
            fulltext = bibjson.get_single_url("fulltext")

            if (fulltext is not None) and not bool(re.match(r"^https?://([^/:]+\.[a-zA-Z]{2,10}|([0-9]{1,3}\.){3}[0-9]{1,3})(:[0-9]+)?(/.*)?$",fulltext)):
                writer.writerow([article.id, bibjson.title, bibjson.get_single_url("fulltext"), article.is_in_doaj()])
