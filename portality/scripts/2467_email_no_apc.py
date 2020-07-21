from portality import models
from portality.core import app
import esprit
import csv

NO_APC = {
    "query": {
        "term": {"index.has_apc.exact": "No"}
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
        writer.writerow(["ID", "Journal Name", "Journal Contact", "Account", "Account Email", "In DOAJ"])

        for j in esprit.tasks.scroll(conn, models.Journal.__type__, q=NO_APC, page_size=100, keepalive='5m'):
            journal = models.Journal(_source=j)
            bibjson = journal.bibjson()
            account = models.Account.pull(journal.owner)

            try:
                writer.writerow([journal.id, bibjson.title, journal.get_latest_contact_email(), account.id, account.email, journal.is_in_doaj()])
            except AttributeError:
                print("Error reading attributes for journal {0}".format(j['id']))
