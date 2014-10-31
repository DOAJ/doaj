from portality import models
from datetime import datetime as dt
from portality import reapplication
from portality.core import app

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

acc = models.Account.all()

for a in acc:
    q = models.SuggestionQuery(owner=a.id)
    suggestions = models.Suggestion.q2obj(q=q)
    if len(suggestions) >= 11:
        filename = a.id + ".csv"
        reapplication.make_csv(app.config.get("BULK_REAPP_PATH") + filename, suggestions)
        bulk_reapp = models.BulkReApplication()
        bulk_reapp.set_spreadsheet_name = filename
        bulk_reapp.set_owner(a.id)
        bulk_reapp.save()








