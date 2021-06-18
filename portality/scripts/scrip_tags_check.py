from portality import models
from portality.core import es_connection
from portality.util import ipt_prefix
import esprit
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

    conn = es_connection

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["es_type", "ID", "Title", "field", "value"])

        for j in esprit.tasks.scroll(conn, ipt_prefix(models.Article.__type__), q=ALL, page_size=100, keepalive='5m'):
            article = models.Article(_source=j)
            results = find_nested("<script>", article.__dict__, [])

            for key, value in results:
                writer.writerow(["article", article.id, article.bibjson().title, key, value])

        for j in esprit.tasks.scroll(conn, ipt_prefix(models.Application.__type__), q=ALL, page_size=100, keepalive='5m'):
            app = models.Application(_source=j)
            results = find_nested("<script>", app.__dict__, [])

            for key, value in results:
                writer.writerow(["application", app.id, app.bibjson().title, key, value])

        for j in esprit.tasks.scroll(conn, ipt_prefix(models.Journal.__type__), q=ALL, page_size=100, keepalive='5m'):
            j = models.Journal(_source=j)
            results = find_nested("<script>", j.__dict__, [])

            for key, value in results:
                writer.writerow(["journal", j.id, j.bibjson().title, key, value])
