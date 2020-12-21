"""
Update journals via CSV for issue e.g. https://github.com/DOAJ/doajPM/issues/2708
twinned with journals_in_doaj_by_account.py
"""

import csv
from portality.models import Journal
from doajtest.fixtures import JournalFixtureFactory

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

            # verify header row with current CSV headers, report errors
            header_row = next(reader)
            expected_headers = JournalFixtureFactory.csv_headers()
            if header_row[1:] != expected_headers:
                print("\nERROR: CSV input file is the wrong format. "
                      "Expected ID column followed by the JournalCSV columns.\n")
                for i in range(0, len(expected_headers)):
                    if expected_headers[i] != header_row[i+1]:
                        print('At column no {0} expected "{1}", found "{2}"'.format(i+1, expected_headers[i], header_row[i+1]))
                exit(1)

            for row in reader:
                print(row)
                # Notify when title has changed?

                success = False

                # Pull by ID
                j = Journal.pull(row[0])

                # Load remaining rows into application form as an update


                # Save the journal
                #j.save()
                writer.writerow([j.id, str(success)])

