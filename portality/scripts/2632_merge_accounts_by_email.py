""" Script for https://github.com/DOAJ/doajPM/issues/2632
 * Assign journals from duplicate accounts to the latest updated account for given email address
 * Delete the unwanted account
"""

from openpyxl import load_workbook
from portality.models import Account, Journal


def merge_accounts_to_latest(acc_list, dry_run=False):
    """ Migrate journals and deduplicate accounts to keep the last updated """
    accs = sorted(acc_list, key=lambda x: x['last_updated'])

    try:
        l_id = accs.pop()['id']
        latest = Account.pull_by_key('id', l_id)
    except IndexError:
        # pop from empty list, we couldn't pull any accounts at all from this group
        return

    if latest is not None:
        print(f'Keeping account {latest.id}')

        for old in accs:
            # First do journal reassignment without initialising the account model
            print(f'Merging account {old["id"]}')
            journals_to_reassign = Journal.get_by_owner(old['id'])

            # I've taken the decision that the bulk edit task is overblown for this, so edit journals in turn
            for j in journals_to_reassign:
                print(f'\tReassigning journal {j.id} from account {old["id"]} to {latest.id}')
                j.set_owner(latest.id)
                if not dry_run:
                    j.save()

            # Initialise the model just to delete it
            old_acc = Account.pull_by_key('id', old['id'])
            if old_acc is not None:
                print(f'\tDeleting account {old_acc.id}')
                if not dry_run:
                    old_acc.delete()
            else:
                print(f'\tNo account found to delete for {old["id"]}')
    else:
        # if latest is None then drop it off and try again with the remaining (any journals assigned won't be updated)
        print(f'Account {l_id} not found, trying next newest')
        merge_accounts_to_latest(accs)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--infile", help="Path to account spreadsheet", required=True)
    parser.add_argument("-s", "--sheet", help="Name of worksheet within the spreadsheet",
                        default='account_email_duplicates_indoaj')
    parser.add_argument("-d", "--dry-run", help="Dry run - output the expected result and exit", action='store_true')
    args = parser.parse_args()

    wb = load_workbook(args.infile)
    sheet = wb[args.sheet]

    rows = sheet.values
    accounts_dict = {}
    # skip the header row
    next(rows)

    for r in rows:
        # Each row is a tuple, headers are ('ID', 'Name', 'Email', 'Created', 'Last Updated')
        # We're going to load these into a dictionary keyed by the email address
        try:
            accounts_dict[r[2]].append({'id': r[0], 'name': r[1], 'last_updated': r[4]})
        except KeyError:
            accounts_dict[r[2]] = [{'id': r[0], 'name': r[1], 'last_updated': r[4]}]

    for e, a in accounts_dict.items():
        print(f'\n{e}')
        merge_accounts_to_latest(a, args.dry_run)
