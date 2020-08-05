"""
This script can be run to generate a CSV output of publisher accounts which do not have th api role set, along
with some useful account information.

```
python accounts_with_missing_api_role.py -o accounts.csv
```
"""
import csv
import esprit
from portality.core import app
from portality import models

MISSING_API_ROLE = {
    "query": {
        "filtered": {
            "query": {
                "term": {
                    "role.exact": "publisher"
                }
            },
            "filter": {
                "not": {
                    "term": {"role.exact": "api"}
                }
            }
        }
    }
}


def publishers_with_journals():
    """ Get accounts for all publishers with journals in the DOAJ """
    for acc in esprit.tasks.scroll(conn, 'account', q=MISSING_API_ROLE, page_size=100, keepalive='1m'):
        publisher_account = models.Account(**acc)
        journal_ids = publisher_account.journal
        if journal_ids is not None:
            for j in journal_ids:
                journal = models.Journal.pull(j)
                if journal is not None and journal.is_in_doaj():
                    yield publisher_account
                    break


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
        writer.writerow(["ID", "Name", "Email", "Created", "Last Updated"])

        for account in publishers_with_journals():
            writer.writerow([
                account.id,
                account.name,
                account.email,
                account.created_date,
                account.last_updated
            ])
