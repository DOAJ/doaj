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


def accounts_with_no_journals(conn, csvwriter=None):
    """ Scroll through all accounts, return those with no journal unless they have excluded roles
    :param conn: An Elasticsearch connection
    :param csvwriter: A CSV writer to output the accounts to
    """
    gathered_account_ids = []
    for acc in esprit.tasks.scroll(conn, 'account', page_size=100, keepalive='1m'):
        account = models.Account(**acc)
        if set(account.role).intersection(EXCLUDED_ROLES):
            continue

        issns = models.Journal.issns_by_owner(account.id)
        if len(issns) == 0:
            gathered_account_ids.append(account.id)

            # Write the user summary to CSV if provided
            if csvwriter is not None:
                csvwriter.writerow([
                    account.id,
                    account.name,
                    account.email,
                    account.created_date,
                    account.last_updated,
                    account.role
                ])

        # todo: progress feedback would be nice

    return gathered_account_ids


def delete_accounts_by_id(conn, id_list):
    esprit.raw.bulk_delete(conn, 'account', id_list)


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--report", help="report accounts to CSV (specify filename)")
    parser.add_argument("-i", "--instructions", help="CSV of accounts to delete, ID must be first column")
    args = parser.parse_args()

    conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])

    if args.report and args.instructions:
        print("\nPlease provide EITHER -r or -i arguments with CSV filenames.")
        parser.print_help()
        exit()

    if args.report:
        print("Writing CSV summary of accounts to delete, please wait...")
        with open(args.report, "w", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Email", "Created", "Last Updated", "Roles"])

            accounts_to_delete = accounts_with_no_journals(conn, writer)

        print("Done!")
        exit()

    if args.instructions:
        with open(args.instructions, 'r', encoding="utf-8") as g:
            reader = csv.reader(g)
            accounts_to_delete = []

            # Skip the header row
            next(reader)
            for line in reader:
                accounts_to_delete.append(line[0])

        # Make sure the user is super serious about doing this.
        resp = input("\nDelete {0} Accounts - are you sure? [y/N]\n".format(len(accounts_to_delete)))
        if resp.lower() == 'y':
            # Run the function to remove the field
            print("Deleting accounts... \n")
            delete_accounts_by_id(conn, accounts_to_delete)
            print("Done")
        else:
            print("Better safe than sorry, exiting.")
        exit()

    print("\nPlease specify operation to perform")
    parser.print_help()
    exit(1)
