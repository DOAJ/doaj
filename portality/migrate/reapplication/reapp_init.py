from portality import models
from datetime import datetime as dt
from portality import reapplication
from portality.core import app
import os
import codecs
import csv
from portality.clcsv import UnicodeWriter


def delete_existing_reapp():
    """Note that this cannot be run in isolation, because it leaves behind unresolved current_application fields in journals"""

    # delete all the suggestions
    q = models.SuggestionQuery(statuses=['reapplication', 'submitted']).query()
    models.Suggestion.delete_by_query(query=q)

    # remove all of the current reapplication records
    models.BulkReApplication.delete_all()

def create_reapplication(journal):
    if not isinstance(journal, models.Journal):
        journal = models.Journal.pull(journal)
    if not isinstance(journal, models.Journal):
        print "Unable to resolve Journal from identifier"

    # determine if this is a re-application viable record
    start_date = app.config.get("TICK_THRESHOLD", "2014-03-19T00:00:00Z")
    date_format = "%Y-%m-%dT%H:%M:%SZ"
    d1 = dt.strptime(journal.created_date, date_format)
    d2 = dt.strptime(start_date, date_format)

    if d1 < d2 and journal.is_in_doaj():
        journal.make_reapplication()
    else:
        print "Journal was non-viable for reapplication"
        if d1 >= d2:
            print "Was created more recently than the cut-off date"
        if not journal.is_in_doaj():
            print "Record is not in the public DOAJ dataset"

def create_reapplications_for_account(acc):
    if not isinstance(acc, models.Account):
        acc = models.Account.pull(acc)

    # FIXME: this is pretty inefficient, but it will do for the moment
    all_journals = models.Journal.all_in_doaj()
    start_date = app.config.get("TICK_THRESHOLD", "2014-03-19T00:00:00Z")
    date_format = "%Y-%m-%dT%H:%M:%SZ"

    for_reapplication = []

    for j in all_journals:
        if j.owner != acc.id:
            continue

        d1 = dt.strptime(j.created_date, date_format)
        d2 = dt.strptime(start_date, date_format)
        if d1 < d2:
            for_reapplication.append(j)
        else:
            print "Journal " + j.id + "was non-viable for reapplication - it was created more recently than the cut-off"

    for r in for_reapplication:
        r.make_reapplication()

    # FIXME: also make the csv if relevant


def create_reapplications():
    all_journals = models.Journal.all_in_doaj()
    start_date = app.config.get("TICK_THRESHOLD", "2014-03-19T00:00:00Z")
    date_format = "%Y-%m-%dT%H:%M:%SZ"

    for_reapplication = []

    for j in all_journals:
        d1 = dt.strptime(j.created_date, date_format)
        d2 = dt.strptime(start_date, date_format)
        if d1 < d2:
            for_reapplication.append(j)

    for r in for_reapplication:
        r.make_reapplication()


def make_bulk_reapp_csv():
    acc = models.Account.all()
    failed_bulk_reapps = []
    email_list_10_plus = []
    email_list_less_10 = []
    separator_list = [",", " or ", "/"]
    for a in acc:
        q = models.SuggestionQuery(statuses=['reapplication'], owner=a.id).query()
        suggestions = models.Suggestion.q2obj(q=q, size=30000)
        contact = []
        emails = a.email

        for sep in separator_list:
            if isinstance(emails, basestring):
                if sep in emails:
                    emails = emails.split(sep)

        if len(suggestions) >= 11:
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

            filename = a.id + ".csv"
            filepath = os.path.join(app.config.get("BULK_REAPP_PATH"), filename)

            if os.path.isfile(filepath):
                try:
                    os.remove(filepath)
                except IOError as e:
                    failed_bulk_reapps.append({a.id: e.message})

            reapplication.make_csv(filepath, suggestions)

            bulk_reapp = models.BulkReApplication()
            bulk_reapp.set_spreadsheet_name(filename)
            bulk_reapp.set_owner(a.id)
            bulk_reapp.save()

        elif len(suggestions) > 0:  # only add to the email list if they actually have suggestions at all
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

def main():
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--doaj", action="store_true", help="do all of the reapplications")
    parser.add_argument("-a", "--acc", help="do reapplications for a specific account")
    parser.add_argument("-j", "--journal", help="do reapplications for a specific journal")

    args = parser.parse_args()

    if args.doaj:
        print "Generating Reapplication for entire DOAJ site"
        delete_existing_reapp()
        create_reapplications()
        make_bulk_reapp_csv()
    elif args.acc:
        print "Generating Reapplication for account", args.acc
        create_reapplications_for_account(args.acc)
    elif args.journal:
        print "Generating Reapplication for journal", args.journal
        # FIXME: remove previous reapplication
        create_reapplication(args.journal)

if __name__ == "__main__":
    main()







