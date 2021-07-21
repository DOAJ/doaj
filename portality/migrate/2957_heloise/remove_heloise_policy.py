import csv
from copy import deepcopy

from portality.models import Journal
from portality.settings import BASE_FILE_PATH

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    args = parser.parse_args()

    if not args.out:
        args.out = "out.csv"
        # print("Please specify an output file path with the -o option")
        # parser.print_help()
        # exit()

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(['Journal ID', 'Old Deposit Policy', "New Deposit Policy", "Has Deposit Policy"])

        f = open(BASE_FILE_PATH + "/migrate/2957_heloise/journalID-for-heloise-removal.txt")
        ids = f.readlines()

        for i in ids:
            j = Journal.pull(i.rstrip('\n'))
            if j:
                bib = j.bibjson()
                old_deposit_policy = deepcopy(bib.deposit_policy)
                deposit_policy = bib.deposit_policy
                if 'Héloïse' in deposit_policy:
                    deposit_policy.remove('Héloïse')
                if len(deposit_policy) == 0:
                    bib.has_deposit_policy = False
                j.save()
                writer.writerow([j.id, old_deposit_policy, deposit_policy, bib.has_deposit_policy])
        f.close()
