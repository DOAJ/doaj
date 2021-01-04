"""
Update journals via CSV for issue e.g. https://github.com/DOAJ/doajPM/issues/2708
twinned with journals_in_doaj_by_account.py

This script makes use of the ManEd journal form processor to validate and finalise updates.

Input CSV must have ID as first column, then the JournalCSV columns following. Turn off strict checking with -f to allow
updates from a mis-shapen CSV file.

NOTE: depending on which fields are required, we may need to add new value transformations in the xwalk from
      CSV columns questions back to the form. See portality/crosswalks/journal_questions.py
"""

import csv
from portality.models import Journal
from portality.crosswalks import journal_questions
from doajtest.fixtures import JournalFixtureFactory

from portality.forms.application_forms import JournalFormFactory

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--infile", help="path to journal update spreadsheet", required=True)
    parser.add_argument("-o", "--out", help="output summary file path", required=True)
    parser.add_argument("-f", "--force", help="disable strict checking of CSV structure (enforces all JournalCSV headings", action='store_true')
    parser.add_argument("-v", "--verbose", help="output more info on CSV errors and updated data", action='store_true')
    parser.add_argument("-d", "--dry-run", help="run this script without actually making index changes", action='store_true')
    args = parser.parse_args()

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Updated', 'Changes', 'Errors'])

        with open(args.infile, 'r', encoding='utf-8') as g:
            reader = csv.DictReader(g)

            # verify header row with current CSV headers, report errors
            header_row = reader.fieldnames
            expected_headers = JournalFixtureFactory.csv_headers()
            if header_row[1:] != expected_headers:
                print("\nWARNING: CSV input file is the wrong format. "
                      "Expected ID column followed by the JournalCSV columns.\n")
                if args.verbose:
                    for i in range(0, len(expected_headers)):
                        try:
                            if expected_headers[i] != header_row[i+1]:
                                print('At column no {0} expected "{1}", found "{2}"'.format(i+1, expected_headers[i], header_row[i+1]))
                        except IndexError:
                            print('At column no {0} expected "{1}", found <NO DATA>'.format(i+1, expected_headers[i]))
                if not args.force:
                    print("\nERROR - CSV is wrong shape, exiting. Use --force to do this update anyway (and you know the consequences)")
                    exit(1)
            else:
                print("\nCSV structure check passed.\n")
            print('\nContinuing to update records...\n')

            for row in reader:
                success = False

                # Pull by ID
                j = Journal.pull(row['ID'])
                if j is not None:
                    # Load remaining rows into application form as an update
                    update_form, updates = journal_questions.Journal2QuestionXwalk.question2form(j, row)
                    if args.verbose:
                        print('\n' + j.id)
                        [print(upd) for upd in updates]

                    # validate update_form
                    formulaic_context = JournalFormFactory.context("admin")
                    fc = formulaic_context.processor(
                        formdata=update_form,
                        source=j
                    )

                    if fc.validate():
                        try:
                            if not args.dry_run:
                                # Save the journal
                                fc.finalise()
                                success = True
                        except Exception as e:
                            if args.verbose:
                                print('Failed to finalise: {1}'.format(j.id, str(e)))
                    else:
                        if args.verbose:
                            print('Failed validation - {1}'.format(j.id, fc.form.errors))

                    # Write a report to CSV out file
                    writer.writerow([j.id, str(success), updates, fc.form.errors])
                else:
                    print("WARNING: no journal found for ID {0}".format(row['ID']))
                    writer.writerow([row['ID'], str(success), "NOT FOUND", ''])
