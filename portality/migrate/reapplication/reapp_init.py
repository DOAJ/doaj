from portality import models
from datetime import datetime as dt
from portality import reapplication
from portality.core import app
import os, time
import codecs
import csv
from portality.clcsv import UnicodeWriter

class ReappCsvException(Exception):
    def __init__(self, message, account_id):
        super(ReappCsvException, self).__init__(message)
        self.account_id = account_id

def delete_existing_reapps():
    """Note that this cannot be run in isolation, because it leaves behind unresolved current_application fields in journals"""

    # delete all the suggestions in a reapplication status
    q = models.SuggestionQuery(statuses=['reapplication', 'submitted']).query()
    models.Suggestion.delete_by_query(query=q)
    #models.Suggestion.refresh()

    # remove all of the current reapplication records
    models.BulkReApplication.delete_all()
    # models.BulkReApplication.refresh()

    # FIXME: should probably remove all the old csvs too

    # FIXME: in an ideal world we'd also go through all the journal records and remove the current_application flag

def delete_existing_reapps_for_account(acc):
    if not isinstance(acc, models.Account):
        acc = models.Account.pull(acc)
    if not isinstance(acc, models.Account):
        print "could not resolve account from identifier " + str(acc)

    q = models.SuggestionQuery(statuses=['reapplication', 'submitted'], owner=acc.id).query()
    models.Suggestion.delete_by_query(query=q)

    models.BulkReApplication.delete_by_owner(acc.id)

def delete_existing_reapp(journal):
    if not isinstance(journal, models.Journal):
        journal = models.Journal.pull(journal)
    if not isinstance(journal, models.Journal):
        print "Unable to resolve Journal from identifier " + str(journal)

    if journal.current_application is None:
        return

    # delete the current_application
    models.Suggestion.remove_by_id(journal.current_application)

    # remove the current_application field from the journal
    journal.remove_current_application()
    journal.save()

    #models.Suggestion.refresh()
    #models.Journal.refresh()


def create_reapplications():
    all_journals = models.Journal.all_in_doaj()
    for j in all_journals:
        create_reapplication(j)

def create_reapplications_for_account(acc):
    if not isinstance(acc, models.Account):
        acc = models.Account.pull(acc)
    if not isinstance(acc, models.Account):
        print "could not resolve account from identifier " + str(acc)

    # this is pretty inefficient, but it will do for the moment (there's no method to retrieve by
    # owner, we would have to write a query)
    all_journals = models.Journal.all_in_doaj()
    for j in all_journals:
        if j.owner != acc.id:
            continue
        create_reapplication(j)

def create_reapplication(journal):
    if not isinstance(journal, models.Journal):
        journal = models.Journal.pull(journal)
    if not isinstance(journal, models.Journal):
        print "Unable to resolve Journal from identifier " + str(journal)

    # determine if this is a re-application viable record
    start_date = app.config.get("TICK_THRESHOLD", "2014-03-19T00:00:00Z")
    date_format = "%Y-%m-%dT%H:%M:%SZ"
    d1 = dt.strptime(journal.created_date, date_format)
    d2 = dt.strptime(start_date, date_format)

    if d1 < d2 and journal.is_in_doaj():
        journal.make_reapplication()
        #models.Suggestion.refresh()
        #models.Journal.refresh()
    else:
        print "Journal " + journal.id + " was non-viable for reapplication"
        if d1 >= d2:
            print "...was created more recently than the cut-off date"
        if not journal.is_in_doaj():
            print "..record is not in the public DOAJ dataset"

def make_bulk_reapp_csvs():
    acc = models.Account.all()
    failed_bulk_reapps = []
    email_list_10_plus = []
    email_list_less_10 = []
    separator_list = [",", " or ", "/"]
    for a in acc:
        try:
            made, num = make_csv_for_account(a)
        except ReappCsvException as e:
            failed_bulk_reapps.append({e.account_id : e.message})
            continue

        contact = []
        emails = a.email

        for sep in separator_list:
            if isinstance(emails, basestring):
                if sep in emails:
                    emails = emails.split(sep)

        if made:
            if isinstance(emails, basestring):
                contact.append(a.id)
                contact.append(emails)
                email_list_10_plus.append(contact)
            else:
                for e in emails:
                    e = e.strip()
                    contact.append(a.id)
                    contact.append(e)
                    email_list_10_plus.append(contact)
                    contact = []

        elif num > 0:  # only add to the email list if they actually have suggestions at all
            for sep in separator_list:
                if isinstance(emails, basestring):
                    if sep in emails:
                        emails = emails.split(sep)

            if isinstance(emails, basestring):
                contact.append(a.id)
                contact.append(emails)
                email_list_less_10.append(contact)
            else:
                for e in emails:
                    e = e.strip()
                    contact.append(a.id)
                    contact.append(e)
                    email_list_less_10.append(contact)
                    contact = []

    with codecs.open('email_list_11_plus.csv', 'wb', encoding='utf-8') as csvfile:
        wr_writer = UnicodeWriter(csvfile, quoting=csv.QUOTE_ALL)
        wr_writer.writerows(email_list_10_plus)

    with codecs.open('email_list_less_11.csv', 'wb', encoding='utf-8') as csvfile:
        wr_writer = UnicodeWriter(csvfile, quoting=csv.QUOTE_ALL)
        wr_writer.writerows(email_list_less_10)

    if failed_bulk_reapps:
        print "Failed bulk reapplications"
        print failed_bulk_reapps

def make_csv_for_journal(journal):
    if not isinstance(journal, models.Journal):
        journal = models.Journal.pull(journal)
    if not isinstance(journal, models.Journal):
        print "Unable to resolve Journal from identifier " + str(journal)

    return make_csv_for_account(journal.owner)

def make_csv_for_account(acc):
    if not isinstance(acc, models.Account):
        acc = models.Account.pull(acc)
    if not isinstance(acc, models.Account):
        print "could not resolve account from identifier " + str(acc)

    # ensure there's no bulk reapplication record
    models.BulkReApplication.delete_by_owner(acc.id)

    q = models.SuggestionQuery(statuses=['reapplication', 'submitted'], owner=acc.id).query()
    suggestions = models.Suggestion.q2obj(q=q, size=30000)
    if len(suggestions) < 11:
        return False, len(suggestions)

    filename = acc.id + ".csv"
    filepath = os.path.join(app.config.get("BULK_REAPP_PATH"), filename)

    if os.path.isfile(filepath):
        try:
            os.remove(filepath)
        except IOError as e:
            raise ReappCsvException(e.message, acc.id)

    reapplication.make_csv(filepath, suggestions)

    bulk_reapp = models.BulkReApplication()
    bulk_reapp.set_spreadsheet_name(filename)
    bulk_reapp.set_owner(acc.id)
    bulk_reapp.save()

    return True, len(suggestions)

def main():
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--doaj", action="store_true", help="do all of the reapplications")
    parser.add_argument("-a", "--acc", help="do reapplications for a specific account")
    parser.add_argument("-j", "--journal", help="do reapplications for a specific journal")

    args = parser.parse_args()

    if args.doaj:
        print "Generating Reapplication for entire DOAJ site"
        delete_existing_reapps()
        time.sleep(2)
        create_reapplications()
        time.sleep(2)
        make_bulk_reapp_csvs()
    elif args.acc:
        print "Generating Reapplication for account", args.acc
        delete_existing_reapps_for_account(args.acc)
        time.sleep(2)
        create_reapplications_for_account(args.acc)
        time.sleep(2)
        make_csv_for_account(args.acc)
    elif args.journal:
        print "Generating Reapplication for journal", args.journal
        delete_existing_reapp(args.journal)
        time.sleep(2)
        create_reapplication(args.journal)
        time.sleep(2)
        make_csv_for_journal(args.journal)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()







