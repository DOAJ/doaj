"""
~~ JournalUpdateByCSV:Script ~~
Update journals via CSV for issue e.g. https://github.com/DOAJ/doajPM/issues/2708
twinned with journals_in_doaj_by_account.py

This script makes use of the ManEd journal form processor to validate and finalise updates.

Input CSV must have ID as first column, then the JournalCSV columns following. Turn off strict checking with -f to allow
updates from a mis-shapen CSV file.

NOTE: depending on which fields are required, we may need to add new value transformations in the xwalk from
      CSV columns questions back to the form. See portality/crosswalks/journal_questions.py

Usage: e.g. for a dry-run first with a malformed CSV
DOAJENV=production python -u journals_update_via_csv.py -i <input_csv_path.csv> -o <output_report_path.csv> -s -f -d > <output_log_path.txt>

Check the report for errors and the output for expected changes, then run without -d to apply the updates
"""

import csv, time
from portality import lock, constants
from portality.core import app
from portality.models import Journal, Account
from portality.crosswalks import journal_questions
from doajtest.fixtures import JournalFixtureFactory

from portality.forms.application_forms import ApplicationFormFactory

from portality.bll import DOAJ
from portality.bll.exceptions import AuthoriseException

SYSTEM_ACCOUNT = {
    "email": "steve@cottagelabs.com",
    "name": "script_journals_csv_update",
    "role": ['admin'],
    "id": "script_journals_csv_update"
}

sys_acc = Account(**SYSTEM_ACCOUNT)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--infile", help="Path to journal update spreadsheet", required=True)
    parser.add_argument("-o", "--out", help="Output summary csv file path", required=True)
    parser.add_argument("-s", "--skip-strict", help="Skip strict checking of CSV structure (JournalCSV headings check)", action='store_true')
    parser.add_argument("-d", "--dry-run", help="Run this script without actually making index changes", action='store_true')
    parser.add_argument("-f", "--force", help="Force update despite failed validation", action='store_true')
    parser.add_argument("-m", "--manual-review", help="Don't finalise the update requests, instead leave open for manual review.", action='store_true')
    args = parser.parse_args()

    # Disable app emails so this doesn't spam users
    app.config['ENABLE_EMAIL'] = False
    app.config['ENABLE_PUBLISHER_EMAIL'] = False

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Changes', 'Errors'])

        # Open with encoding that deals with the Byte Order Mark since we're given files from Windows.
        with open(args.infile, 'r', encoding='utf-8-sig') as g:
            reader = csv.DictReader(g)

            # verify header row with current CSV headers, report errors
            header_row = reader.fieldnames
            expected_headers = JournalFixtureFactory.csv_headers()
            if header_row[1:] != expected_headers:
                print("\nWARNING: CSV input file is the wrong format. "
                      "Expected ID column followed by the JournalCSV columns.\n")
                for i in range(0, len(expected_headers)):
                    try:
                        if expected_headers[i] != header_row[i+1]:
                            print('At column no {0} expected "{1}", found "{2}"'.format(i+1, expected_headers[i], header_row[i+1]))
                    except IndexError:
                        print('At column no {0} expected "{1}", found <NO DATA>'.format(i+1, expected_headers[i]))
                if not args.skip_strict:
                    print("\nERROR - CSV is wrong shape, exiting. Use --force to do this update anyway (and you know the consequences)")
                    exit(1)
            else:
                print("\nCSV structure check passed.\n")
            print('\nContinuing to update records...\n')

            # ~~ ->$JournalUpdateByCSV:Feature ~~
            for row in reader:
                # Pull by ID
                j = Journal.pull(row['ID'])
                if j is not None:
                    print('\n' + j.id)
                    # Load remaining rows into application form as an update
                    # ~~ ^->JournalQuestions:Crosswalk ~~
                    update_form, updates = journal_questions.Journal2QuestionXwalk.question2form(j, row)
                    if len(updates) > 0:
                        [print(upd) for upd in updates]

                        # Create an update request for this journal
                        update_req = None
                        jlock = None
                        alock = None
                        try:
                            # ~~ ^->UpdateRequest:Feature ~~
                            update_req, jlock, alock = DOAJ.applicationService().update_request_for_journal(j.id, account=j.owner_account)
                        except AuthoriseException as e:
                            print('Could not create update request: {0}'.format(e.reason))
                            writer.writerow([j.id, ' | '.join(updates), 'COULD NOT UPDATE - ' + str(e.reason)])
                            continue
                        except lock.Locked as e:
                            print('Could not edit journal - locked.')
                            writer.writerow([j.id, ' | '.join(updates), 'JOURNAL LOCKED - ' + str(e)])
                            continue

                        # validate update_form - portality.forms.application_processors.PublisherUpdateRequest
                        # ~~ ^->UpdateRequest:FormContext ~~
                        formulaic_context = ApplicationFormFactory.context("update_request")
                        fc = formulaic_context.processor(
                            formdata=update_form,
                            source=update_req
                        )

                        if not fc.validate():
                            print('Failed validation - {0}'.format(fc.form.errors))
                            failed_on_supplied = False  # todo: ignore validation on fields that aren't supplied

                            if (not args.force) or failed_on_supplied:
                                # Write a report to CSV out file
                                writer.writerow([j.id, ' | '.join(updates), fc.form.errors])
                                continue
                            elif not args.dry_run:
                                print('Strict mode not requested, applying update...')

                        try:
                            if not args.dry_run:
                                # Save the update request
                                fc.finalise(email_alert=False)
                                print('Update request created.')

                                if not args.manual_review:
                                    # This is the update request, in 'update request' state
                                    update_req_for_review = fc.target

                                    # Create an Admin update request review form - portality.forms.application_processors.AdminApplication
                                    # ~~ ^->ManEdApplication:FormContext ~~
                                    formulaic_context2 = ApplicationFormFactory.context("admin")
                                    fc2 = formulaic_context2.processor(
                                        source=update_req_for_review
                                    )

                                    # Accept the update request, and finalise to complete the changes
                                    fc2.form.application_status.data = constants.APPLICATION_STATUS_ACCEPTED
                                    fc2.finalise(sys_acc, email_alert=False)
                                    print('Automatic review. Journal has been updated.')
                        except Exception as e:
                            writer.writerow([j.id, ' | '.join(updates), 'COULD NOT FINALISE - ' + str(e)])
                            print('Failed to finalise: {1}'.format(j.id, str(e)))
                            raise
                        finally:
                            if jlock is not None:
                                jlock.delete()
                            if alock is not None:
                                alock.delete()
                    else:
                        updates = ['NO CHANGES']
                else:
                    print("\nWARNING: no journal found for ID {0}".format(row['ID']))
                    writer.writerow([row['ID'], "NOT FOUND", ''])
