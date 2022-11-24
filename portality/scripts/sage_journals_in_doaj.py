from portality import models
from portality.core import app
import csv

SAGE_JOURNALS_IN_DOAJ = {
    "query": {
        "bool": {
            "filter": {
                "bool": {
                    "must": [
                        {"term": {"index.publisher.exact": "SAGE Publishing"}},
                        {"term": {"admin.in_doaj": True}}
                    ]
                }
            }
        }
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

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID",
                         "Title"])

        for journal in Journal.scroll(q=SAGE_JOURNALS_IN_DOAJ, page_size=100, keepalive='5m', limit=800):
            bibjson = journal.bibjson()

            writer.writerow([journal.id,
                             bibjson.title
                             ])
