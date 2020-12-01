"""
This script can be run to generate a CSV output of publisher accounts which do not have th api role set, along
with some useful account information. Using the flag -a adds the missing API role and key to those accounts.

```
python accounts_with_missing_api_role.py -o accounts.csv [-a]
```
"""
import csv
import esprit
from portality.core import es_connection
from portality.util import ipt_prefix
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
    for acc in esprit.tasks.scroll(conn, ipt_prefix('account'), q=MISSING_API_ROLE, page_size=100, keepalive='1m'):
        publisher_account = models.Account(**acc)
        issns = models.Journal.issns_by_owner(publisher_account.id)
        if len(issns) > 0:
            yield publisher_account


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path", required=True)
    parser.add_argument('-a', '--add', help="add the missing role", action='store_true')
    args = parser.parse_args()

    if not (args.out or args.add):
        print("Please specify an output file path with the -o option, or optionally add role with -a")
        parser.print_help()
        exit()

    conn = es_connection

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Email", "Created", "Last Updated", "Roles"])

        for account in publishers_with_journals():
            if args.add:
                account.add_role('api')
                account.generate_api_key()
                account.save()

            writer.writerow([
                account.id,
                account.name,
                account.email,
                account.created_date,
                account.last_updated,
                account.role
            ])
