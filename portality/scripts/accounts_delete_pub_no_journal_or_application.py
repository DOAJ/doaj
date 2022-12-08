"""
Delete all non-editorial user accounts who are not the owner of a journal, application, update request, or draft.

python accounts_delete_pub_no_journal_or_application.py [-r deletion_report.csv] [-o older_than_date]
"""

import csv
from portality import models
from portality.lib import dates

# set of roles to exclude from the deletes
EXCLUDED_ROLES = {'associate_editor', 'editor', 'admin', 'ultra_bulk_delete', 'jct_inprogress'}


def accounts_with_no_journals_or_applications(csvwriter=None, older_than=dates.now_with_microseconds()):
    """ Scroll through all accounts, return those with no journal unless they have excluded roles
    :param older_than: Exclude accounts newer than the supplied datestamp
    :param csvwriter: A CSV writer to output the accounts to
    """
    gathered_account_ids = []
    for account in models.Account.iterate():
        if set(account.role).intersection(EXCLUDED_ROLES):
            continue

        # An newer date will have a negative timedelta
        if account.created_date is not None:
            if (dates.parse(older_than) - dates.parse(account.created_date)).days < 0:
                continue

        issns = models.Journal.issns_by_owner(account.id)
        apps = models.Application.get_by_owner(account.id)  # Applications and URs
        drafts = models.DraftApplication.get_by_owner(account.id)

        if len(issns) == len(apps) == len(drafts) == 0:
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

    return gathered_account_ids


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--report", help="report accounts to CSV (specify filename)")
    parser.add_argument("-o", "--older_than", default=dates.now_with_microseconds())
    parser.add_argument("-i", "--instructions", help="CSV of accounts to delete, ID must be first column")
    args = parser.parse_args()

    if args.report and args.instructions:
        print("\nPlease provide EITHER -r or -i arguments with CSV filenames.")
        parser.print_help()
        exit()

    if args.report:
        print("Writing CSV summary of accounts to delete, please wait...")
        with open(args.report, "w", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Email", "Created", "Last Updated", "Roles"])

            accounts_to_delete = accounts_with_no_journals_or_applications(writer, args.older_than)

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
            models.Account.bulk_delete(accounts_to_delete)
            print("Done")
        else:
            print("Better safe than sorry, exiting.")
        exit()

    print("\nPlease specify operation to perform")
    parser.print_help()
    exit(1)
