from portality import models
from portality.core import es_connection
from portality.util import ipt_prefix
import esprit
import csv

ALL = {
    "query": {
        "match_all": {}
    }
}


def remove_trailing_whitespaces(d, values):
    for key, value in d.items():
        if isinstance(value, dict):
            return remove_trailing_whitespaces(value, values)
        if isinstance(value, str):
            d[key] = value.strip()
            if value != d[key]:
                values.append({"key": key, "old value": value, "new value": d[key]})
    return values

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
        writer.writerow(["es_type", "ID", "key", "old value", "new value"])

        for j in esprit.tasks.scroll(conn, ipt_prefix(models.Article.__type__), q=ALL, page_size=100, keepalive='5m'):
            article = models.Article(_source=j)
            results = remove_trailing_whitespaces(article.__dict__, [])

            for i in results:
                writer.writerow(["article", article.id, results["key"], results["old value"], results["new value"]])

        for j in esprit.tasks.scroll(conn, ipt_prefix(models.Journal.__type__), q=ALL, page_size=100, keepalive='5m'):
            journal = models.Journal(_source=j)
            results = remove_trailing_whitespaces(journal.__dict__, [])

            for key, value in results:
                writer.writerow(["journal", journal.id, results["key"], results["old value"], results["new value"]])
