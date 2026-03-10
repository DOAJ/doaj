from portality import models, constants
import csv

query = {
    "query": {
        "bool": {
            "must": [
                {
                    "term": {
                        "admin.application_status.exact": constants.APPLICATION_STATUS_ACCEPTED
                    }
                },
                {
                    "range": {
                        "created_date": {
                            "gte": "2018-08-01T00:00:00Z"
                        }
                    }
                }
            ]
        }
    }
}

with open("application_journal_integrity_report.csv", "w", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Application ID", "Created Date", "Last Updated", "Journal ID", "Issue"])

    for application in models.Application.iterate_unstable(query):
        rj = application.related_journal
        if rj is None:
            print([application.id, application.created_date, application.last_manual_update, "", "Accepted application has no related_journal"])
            writer.writerow([application.id, application.created_date, application.last_manual_update, "", "Accepted application has no related_journal"])
            continue

        journal = models.Journal.pull(rj)
        if journal is None:
            print([application.id, application.created_date, application.last_manual_update, rj, "Accepted application has related_journal that does not exist"])
            writer.writerow([application.id, application.created_date, application.last_manual_update, rj, "Accepted application has related_journal that does not exist"])
            continue