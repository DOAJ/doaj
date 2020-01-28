import requests

from portality import models
from portality.core import app
import esprit
import re
import csv

INVALID_URLS = {
        "query": {
            "match_all": {}
        }
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

    conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID"])

        for j in esprit.tasks.scroll(conn, models.Journal.__type__, q=INVALID_URLS, page_size=100, keepalive='5m'):
            journal = models.Journal(_source=j)
            r = requests.get("http://doaj.org/api/v1/journals/{}".format(journal.id))
            if r.status_code == 500:
                writer.writerow([journal.id, r.status_code])
