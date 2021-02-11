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
    writer.writerow([
        "application", "app_created", "app_last_update", "app_last_manual_update", "app_adjusted_lmu", "app_issns",
        "journal_matches", "journal", "journal_created", "journal_reapp", "journal_issns",
        "jc_ac_diff", "jc_lmua_diff", "mc1", "lra_ac_diff", "mc2",
        "is_match", "reason"
    ])

    # first, get each application and consider it
    counter = 0
    for result in esprit.tasks.scroll(conn, "suggestion", keepalive="1m"):
        counter += 1
        application = Suggestion(**result)
        application.remove_related_journal()

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
            related_journals = sorted(related_journals, key=lambda j: j.created_timestamp)

            # we set an application as having a related journal in the following conditions:
            # 1. The application was created before the journal and last updated near or after the journal created date,
            #       and this journal is the nearest one in time
            # 2. The last_reapplication date is after the application created date, and is the nearest one
            app_created = application.created_timestamp
            for journal in related_journals:
                almu = application.last_manual_update_timestamp
                almu_adjusted = dates.after(almu, 3600)

                # do a load of reporting prep
                jc_ac_diff = int((journal.created_timestamp - app_created).total_seconds())
                jc_lmua_diff = int((journal.created_timestamp - almu_adjusted).total_seconds())
                row = [
                    application.id, application.created_date, application.last_updated, application.last_manual_update,
                    almu_adjusted.strftime("%Y-%m-%dT%H:%M:%SZ"), ",".join(issns),
                    str(len(related_journals)), journal.id, journal.created_date, journal.data.get("last_reapplication", ""), ",".join(journal.bibjson().issns()),
                    str(jc_ac_diff), str(jc_lmua_diff), "false"
                ]
                if journal.data.get("last_reapplication") is not None:
                    lr = journal.data.get("last_reapplication")
                    lrd = datetime.strptime(lr, "%Y-%m-%dT%H:%M:%SZ")
                    lra_ac_diff = int((lrd - app_created).total_seconds())
                    row.append(str(lra_ac_diff))
                    row.append("false")
                else:
                    row.append("")
                    row.append("false")

                # now make some decisions about whether/how to link this application
                if (journal.created_timestamp > application.created_timestamp
                        #and almu >= journal.created_timestamp):
                        and almu_adjusted >= journal.created_timestamp):
                    application.set_related_journal(journal.id)
                    row[13] = "true"
                    row[15] = ""
                    row += ["yes", "journal created after application, application last (manual) update after journal create"]
                    writer.writerow(row)
                    break
                elif journal.data.get("last_reapplication") is not None:
                    lr = journal.data.get("last_reapplication")
                    lrd = datetime.strptime(lr, "%Y-%m-%dT%H:%M:%SZ")
                    if lrd > app_created:
                        application.set_related_journal(journal.id)
                        row[13] = ""
                        row[15] = "true"
                        row += ["yes", "last reapplication date more recent than application created date"]
                        writer.writerow(row)
                        break
                    else:
                        row += ["no", "last reapplication date earlier than application created date"]
                        writer.writerow(row)
                else:
                    row += ["no", "no reapplication date, and journal either created before application created, or application not (manually) updated since journal created date"]
                    writer.writerow(row)

            application.save()
            print((counter, application.id))
        else:
            row = [
                application.id, application.created_date, application.last_updated, application.last_manual_update, "", ",".join(issns),
                "0", "", "", "", "", "", "", "", "", "", ""
            ]
            writer.writerow(row)
            print((counter, application.id))

# let the index catch up
time.sleep(2)

rows = []
# longest_row = 0

# now go through all the journals, and consider their related applications
counter = 0
for result in esprit.tasks.scroll(conn, "journal", keepalive="1m"):
    counter += 1
    journal = Journal(**result)
    journal.remove_related_applications()

    # find all the applications that have this journal as a related_journal
    # this query returns them ordered oldest first
    applications = Suggestion.find_all_by_related_journal(journal.id)

    if len(applications) > 0:
        for application in applications:
            row = [
                journal.id, journal.created_date, journal.data.get("last_reapplication", ""),
                application.id, application.application_status, application.created_date
            ]

            if application.application_status != "accepted":
                row += ["", "no", "application is not in status 'accepted'"]
                rows.append(row)
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

            row += [date_accepted, "yes", "application is in status 'accepted' and refers to the journal as a related journal"]
            rows.append(row)

        journal.save()

    else:
        row = [
            journal.id, journal.created_date, journal.data.get("last_reapplication", ""),
            "", "", "", "", "no", "no application refers to this journal as a related journal"
        ]
        rows.append(row)

    print((counter, journal.id))

with open("journal_2_application.csv", "wb") as f:
    writer = csv.writer(f)
    header = [
        "journal", "journal_created", "journal_reapp",
        "application", "application_status", "application_created", "date_accepted",
        "recorded?", "reason"
    ]

    writer.writerow(header)
    for row in rows:
        writer.writerow(row)





