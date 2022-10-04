from portality import models
from portality.core import app
from portality.models import Journal
import csv

NO_APC = {
    "query": {
        "bool": {
            "filter": {
                "bool": {
                    "must": {
                        "term": {"admin.in_doaj": True}
                    }
                }
            },
            "must": {
                "term": {"index.has_apc.exact": "No"}
            }
        }
    }
}

if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    args = parser.parse_args()

    args.out = "out.txt"

    # if not args.out:
    #     print("Please specify an output file path with the -o option")
    #     parser.print_help()
    #     exit()

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Journal Name", "Journal Contact", "Account", "Account Email", "Marketing Consent"])

        for journal in Journal.scroll(q=NO_APC, page_size=100, keepalive='5m'):
            bibjson = journal.bibjson()
            account = models.Account.pull(journal.owner)

            try:
                writer.writerow([journal.id, bibjson.title, journal.get_latest_contact_email(), account.id, account.email, account.marketing_consent])
            except AttributeError:
                print("Error reading attributes for journal {0}".format(j['id']))
