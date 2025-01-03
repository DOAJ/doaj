from portality import models
from portality.util import ipt_prefix
import csv


NOT_IN_DOAJ = {
    "query" : {
        "bool" : {
            "must" : [
                {"term" : {"admin.in_doaj" : False}}
            ]
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

    conn = es_connection

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Journal Name", "E-ISSN", "P-ISSN", "Article Count"])

        for journal in Journal.scroll(q=ALL, page_size=100, keepalive='5m'):
            bibjson = journal.bibjson()
            issns = bibjson.issns()
            count = models.Article.count_by_issns(issns)

            if count > 0:
                writer.writerow([journal.id, bibjson.title, bibjson.get_one_identifier(bibjson.E_ISSN), bibjson.get_one_identifier(bibjson.P_ISSN), count])
