from portality import models
from portality.core import es_connection
import esprit
import csv
from portality.util import ipt_prefix

EMPTY_ISSN = {
"query": {
        "bool": {
            "filter": {
                "bool": {
                    "must": {
                        "term": {"admin.in_doaj": "true"}
                    }
                }
            }
        }
    }
}

if __name__ == "__main__":

    # import argparse
    # parser = argparse.ArgumentParser()
    # parser.add_argument("-o", "--out", help="output file path")
    # args = parser.parse_args()
    #
    # if not args.out:
    #     print("Please specify an output file path with the -o option")
    #     parser.print_help()
    #     exit()

    out = "out.csv"

    with open(out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "PISSN", "EISSN"])
        count = 0
        for j in esprit.tasks.scroll(es_connection, ipt_prefix(models.Journal.__type__), q=EMPTY_ISSN, page_size=100, keepalive='5m'):
            journal = models.Journal(_source=j)
            count = count + 1
            pissn = journal.bibjson().get_one_identifier("pissn")
            eissn = journal.bibjson().get_one_identifier("eissn")
            if pissn == "" or eissn == "":
                try:
                    writer.writerow([journal.id, pissn, eissn])
                except AttributeError:
                    print("Error reading attributes for journal {0}".format(j['id']))
        print ("Analyzed {} journals in DOAJ".format(count))
