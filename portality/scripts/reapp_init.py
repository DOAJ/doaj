from portality import models
from datetime import datetime as dt
from portality import reapplication
from portality.core import app
import os

def create_reapplications():
    all_journals = models.Journal.all_in_doaj()
    start_date = "2014-03-19T00:00:00Z"
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
    for a in acc:
        q = models.SuggestionQuery(owner=a.id).query()
        suggestions = models.Suggestion.q2obj(q=q)
        if len(suggestions) >= 4:
            filename = a.id + ".csv"
            filepath = os.path.join(app.config.get("BULK_REAPP_PATH"), filename)

            if os.path.isfile(filepath):
                try:
                    os.remove(filepath)
                except IOError as e:
                    failed_bulk_reapps.append({a.id : e.message})

            reapplication.make_csv(filepath, suggestions)

            bulk_reapp = models.BulkReApplication()
            bulk_reapp.set_spreadsheet_name = filename
            bulk_reapp.set_owner(a.id)
            bulk_reapp.save()


    if failed_bulk_reapps:
        print "Failed bulk reapplications"
        print failed_bulk_reapps

def main():
    create_reapplications()
    make_bulk_reapp_csv()

if __name__ == "__main__":
    main()







