"""
Update journals via CSV for issue e.g. https://github.com/DOAJ/doajPM/issues/2708
twinned with journals_in_doaj_by_account.py
"""

import csv
from portality.models import Journal

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--infile", help="path to journal update spreadsheet", required=True)
    parser.add_argument("-o", "--out", help="output summary file path", required=True)
    args = parser.parse_args()

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Status'])

        with open(args.infile, 'r', encoding='utf-8') as g:
            reader = csv.reader(g)

            for row in reader:
                # verify header row with current CSV headers

                success = False

                # Pull by ID
                j = Journal.pull(row[0])

                # Load remaining rows into application form as an update

                # Save the journal
                j.save()
                writer.writerow([j.id, str(success)])

