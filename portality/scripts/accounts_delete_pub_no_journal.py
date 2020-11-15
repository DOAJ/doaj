"""
Delete all non-editorial user accounts not assigned to a journal

python accounts_delete_pub_no_journal.py [-r deletion_report.csv]
"""

import esprit
import csv
from portality.core import app
from portality import models

# set of roles to exclude from the deletes
EXCLUDED_ROLES = {'associate_editor', 'editor', 'admin', 'ultra_bulk_delete'}


def accounts_with_no_journals(conn):
    """ Scroll through all accounts, return those with no journal unless they have excluded roles """
    gathered_account_ids = []
    for acc in esprit.tasks.scroll(conn, 'account', page_size=100, keepalive='1m'):
        account = models.Account(**acc)
        if set(account.role).intersection(EXCLUDED_ROLES):
            continue

        issns = models.Journal.issns_by_owner(account.id)
        if len(issns) == 0:
            gathered_account_ids.append(account.id)

    return gathered_account_ids


def delete_accounts_by_id(conn, id_list):
    esprit.raw.bulk_delete(conn, 'account', id_list)


def write_csv(filename, id_list):
    with open(filename, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Email", "Created", "Last Updated", "Roles"])

        for _id in id_list:
            account = models.Account.pull(_id)
            writer.writerow([
                account.id,
                account.name,
                account.email,
                account.created_date,
                account.last_updated,
                account.role
            ])


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--report", help="report accounts to CSV (specify filename)")
    args = parser.parse_args()

    conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])

    accounts_to_delete = accounts_with_no_journals(conn)

    if args.report:
        print("Writing CSV summary of accounts to delete")
        write_csv(args.report, accounts_to_delete)
        exit()

    # Make sure the user is super serious about doing this.
    resp = input("\nDelete {0} Accounts - are you sure? [y/N]\n".format(len(accounts_to_delete)))
    if resp.lower() == 'y':
        # Run the function to remove the field
        print("Deleting the following accounts... \n")
        [print(a) for a in accounts_to_delete]
        delete_accounts_by_id(conn, accounts_to_delete)
    else:
        print("Better safe than sorry, exiting.")
