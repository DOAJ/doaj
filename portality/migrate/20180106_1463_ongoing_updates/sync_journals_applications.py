import esprit, time, csv
from portality.core import app
from portality.models import Suggestion, Journal
from datetime import datetime
from portality.lib import dates

source = {
    "host": app.config.get("ELASTIC_SEARCH_HOST"),
    "index": app.config.get("ELASTIC_SEARCH_DB")
}

conn = esprit.raw.Connection(source.get("host"), source.get("index"))

with open("application_2_journal.csv", "wb") as f:
    writer = csv.writer(f)
    writer.writerow(["application", "journal"])

    # first, get each application and consider it
    counter = 0
    for result in esprit.tasks.scroll(conn, "suggestion", keepalive="1m"):
        counter += 1
        application = Suggestion(**result)

        # find all the journals that this application could be associated with (which we need to do by issn)
        issns = application.bibjson().issns()

        # query by each issn individually, because we're looking for the widest possible map.  Querying by
        # both would require both issns match
        related_journals = []
        related_journal_ids = []
        for issn in issns:
            journals = Journal.find_by_issn(issn)
            for journal in journals:
                if journal.id not in related_journal_ids:
                    related_journal_ids.append(journal.id)
                    related_journals.append(journal)

        if len(related_journals) > 0:
            # sort the journals by their created date
            sorted(related_journals, key=lambda j: j.created_timestamp)

            # we set an application as having a related journal in the following conditions:
            # 1. The application was created before the journal and last updated near or after the journal created date,
            #       and this journal is the nearest one in time
            # 2. The last_reapplication date is after the application created date, and is the nearest one
            app_created = application.created_timestamp
            for journal in related_journals:
                almu = application.last_manual_update_timestamp
                almu_adjusted = dates.after(almu, 3600)
                if (journal.created_timestamp > application.created_timestamp
                        and almu >= journal.created_timestamp
                        and almu_adjusted >= journal.created_timestamp):
                    application.set_related_journal(journal.id)
                    break
                elif journal.data.get("last_reapplication") is not None:
                    lr = journal.data.get("last_reapplication")
                    lrd = datetime.strptime(lr, "%Y-%m-%dT%H:%M:%SZ")
                    if lrd > app_created:
                        application.set_related_journal(journal.id)
                        break

            application.save()
            row = [application.id, application.related_journal]
            writer.writerow(row)
            print(counter, row)
        else:
            row = [application.id, ""]
            writer.writerow(row)
            print(counter, row)

# let the index catch up
time.sleep(2)

rows = []
longest_row = 0

# now go through all the journals, and consider their related applications
counter = 0
for result in esprit.tasks.scroll(conn, "journal", keepalive="1m"):
    counter += 1
    journal = Journal(**result)
    journal.remove_related_applications()

    # find all the applications that have this journal as a related_journal
    # this query returns them ordered oldest first
    applications = Suggestion.find_all_by_related_journal(journal.id)

    for application in applications:
        if application.application_status != "accepted":
            continue
        date_accepted = None
        acreated = application.created_timestamp
        jcreated = journal.created_timestamp
        jreapp_str = journal.data.get("last_reapplication")
        jreapp = None
        if jreapp_str is not None:
            jreapp = datetime.strptime(jreapp_str, "%Y-%m-%dT%H:%M:%SZ")

        if acreated < jcreated:
            date_accepted = journal.created_date
        elif jreapp is not None and acreated < jreapp:
            date_accepted = jreapp_str
        else:
            date_accepted = application.created_date

        journal.add_related_application(application.id, date_accepted)

    journal.save()

    row = [journal.id]
    for record in journal.related_applications:
        row.append(record.get("application_id"))
        row.append(record.get("date_accepted"))
    if len(row) > longest_row:
        longest_row = len(row)
    rows.append(row)

    print(counter, row)

with open("journal_2_application.csv", "wb") as f:
    writer = csv.writer(f)
    header = ["journal"]
    pairs = longest_row - 1
    for i in range(0, pairs, 2):
        header.append("application")
        header.append("date_accepted")

    writer.writerow(header)

    for row in rows:
        writer.writerow(row)





