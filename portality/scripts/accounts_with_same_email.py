"""
This script can be run to generate a CSV output of accounts which have the same email address

```
python accounts_with_same_email.py -o accounts_email.csv [-a]
```
"""
import csv
import esprit
from portality.core import es_connection
from portality.util import ipt_prefix
from portality import models

HAS_EMAIL = {
    "query": {
        "filtered": {
            "query": {
                "match_all": {}
            },
            "filter": {
                "exists": {"field": "email"}
            }
        }
    }
}


def users_with_emails():
    for acc in esprit.tasks.scroll(conn, ipt_prefix('account'), q=HAS_EMAIL, page_size=100, keepalive='1m'):
        yield models.Account(**acc)


def users_with_journals_and_emails():
    """ Get accounts for all users with journals in the DOAJ """
    for acc in esprit.tasks.scroll(conn, ipt_prefix('account'), q=HAS_EMAIL, page_size=100, keepalive='1m'):
        acct = models.Account(**acc)
        journal_ids = acct.journal
        if journal_ids is not None:
            for j in journal_ids:
                journal = models.Journal.pull(j)
                if journal is not None and journal.is_in_doaj():
                    yield acct
                    break


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    parser.add_argument("-a", "--all", help="all users (defaults to users with journals in doaj)", action="store_true")
    args = parser.parse_args()

    if not args.out:
        print("Please specify an output file path with the -o option")
        parser.print_help()
        exit()

    conn = es_connection

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Email", "Created", "Last Updated"])

        # A dict of email: id for all accounts
        emails_seen = {}
        # To minimise how many accounts we need to initialise a second time, keep a set of ids to write to the csv
        duplicated_ids = set()

        users = users_with_emails() if args.all else users_with_journals_and_emails()

        for account in users:
            # for simplicity we just write out our account with duplicated email when found, sort later via spreadsheet
            if account.email in emails_seen:
                writer.writerow([
                    account.id,
                    account.name,
                    account.email,
                    account.created_date,
                    account.last_updated
                ])
                duplicated_ids.add(emails_seen[account.email])
            else:
                emails_seen[account.email] = account.id

        # Write additional rows containing those records found first that have duplicated emails
        for _id in duplicated_ids:
            a = models.Account.pull(_id)
            writer.writerow([
                a.id,
                a.name,
                a.email,
                a.created_date,
                a.last_updated
            ])
