from portality import models
from portality.util import ipt_prefix
import csv

ALL = {
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

    conn = es_connection

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Article Title", "PISSN", "EISSN"])

        for article in models.Article.scroll(q=ALL, page_size=100, keepalive='5m'):
            bibjson = article.bibjson()
            pissn = bibjson.get_one_identifier("pissn")
            eissn = bibjson.get_one_identifier("eissn")

            if pissn == eissn:
                writer.writerow([article.id, bibjson.title, pissn, eissn])
