from portality.models import Article, Application, Journal
from portality.util import ipt_prefix
import re
import csv

ALL = {
    "query": {
        "match_all": {}
    }
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

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["es_type", "ID", "Title", "field", "value"])

        for art in Article.scroll(q=ALL, page_size=100, keepalive='5m'):
            results = find_nested("<script>", art.__dict__, [])

            for key, value in results:
                writer.writerow(["article", article.id, article.bibjson().title, key, value])

        for app in Application.scroll(q=ALL, page_size=100, keepalive='5m'):
            results = find_nested("<script>", app.__dict__, [])

            for key, value in results:
                writer.writerow(["application", app.id, app.bibjson().title, key, value])

        for j in Journal.scroll(q=ALL, page_size=100, keepalive='5m'):
            results = find_nested("<script>", j.__dict__, [])

            for key, value in results:
                writer.writerow(["journal", j.id, j.bibjson().title, key, value])
