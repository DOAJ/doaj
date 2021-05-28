from portality import models
from portality.core import es_connection
from portality.util import ipt_prefix
import esprit
import re
import csv

ALL_ARTICLES = {
    "query": {
        "match_all": {}
    },
    "sort": [{
        "in_doaj": "desc"
    }]
}


def find_nested(substr, d, result):
    for key, value in d.items():
        if isinstance(value, dict):
            return find_nested(substr, value, result)
        if isinstance(value, str) and substr in value:
            print("found! {" + key + ": " + value + "}")
            result.append({key, value})
    return result


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    args = parser.parse_args()

    if not args.out:
        print("Please specify an output file path with the -o option")
        parser.print_help()
        exit()

    conn = es_connection

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Article Title", "field", "value"])

        for j in esprit.tasks.scroll(conn, ipt_prefix(models.Article.__type__), q=ALL_ARTICLES, page_size=100, keepalive='5m'):
            article = models.Article(_source=j)
            print("Analyzing article: " + article.id)
            results = find_nested("<script>", article.__dict__, [])

            for key, value in results:
                writer.writerow([article.id, article.bibjson().title, key, value])
