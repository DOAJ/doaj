import csv

from portality.models import Journal
from portality.settings import BASE_FILE_PATH

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    args = parser.parse_args()

    if not args.out:
        print("Please specify an output file path with the -o option")
        parser.print_help()
        exit()

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)

        f = open(BASE_FILE_PATH + "/scripts/resources/journalID-for-heloise-removal.txt")
        ids = f.readlines()

        for i in ids:
            j = Journal.pull(i.rstrip('\n'))
            print(j.bibjson().deposit_policy)
            if j:
                deposit_policy = j.bibjson().deposit_policy
                if 'Héloïse' in deposit_policy:
                    deposit_policy.remove('Héloïse')
                    j.save(blocking=True)
                    writer.writerow("Journal {} modified and saved.".format(j.id))
        f.close()
