"""
S.E. 2026-05-20

Scroll through all Journals in DOAJ to write a CSV of owner accounts with contact details.
https://github.com/DOAJ/doajPM/issues/4371
"""


from portality.models import Journal, Account
import csv

# Record an {account_id: [journal_ids]} map so that we can reduce lookups on the Account index
owner_map = {}

if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path", default="4371_accounts_with_journals.csv")
    args = parser.parse_args()

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Account ID", "Created Date", "Account Name", "Email", "Journal IDs"])

        for j in Journal.all_in_doaj():
            owner = j.owner
            try:
                owner_map[owner].append(j.id)
            except KeyError:
                owner_map[owner] = [j.id]

        for o, js in owner_map.items():
            acc = Account.pull(o)
            if acc is None:
                print('No account with id', o)
                continue

            writer.writerow([o, acc.created_date, acc.name, acc.email, *js])

    print('Written to', args.out)
