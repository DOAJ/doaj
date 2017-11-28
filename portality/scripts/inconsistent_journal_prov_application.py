"""
Script which attempts to identify journals, applications and provenance records which show an inconsistent state:

1. All suggestions where there are provenance records from a later time

2. All accepted suggestions where the journal hasn't been created

3. All journals for which the created_date is inconsistent with the application's last_updated date, and for which there are edit and/or accepted provenance records

4. All journals for which the related account is missing
"""

from portality.core import app
from portality.models import Suggestion, Provenance, Journal, Account
from portality.clcsv import UnicodeWriter
import esprit, codecs, csv
from datetime import datetime
from copy import deepcopy

TIMEZONE_CUTOFF = datetime.strptime("2017-05-18T14:02:08Z", "%Y-%m-%dT%H:%M:%SZ")
THRESHOLD = 20.0

source = {
    "host": app.config.get("ELASTIC_SEARCH_HOST"),
    "index": app.config.get("ELASTIC_SEARCH_DB")
}
local = esprit.raw.Connection(source.get("host"), source.get("index"))

#live = esprit.raw.Connection(app.config.get("DOAJGATE_URL"), "doaj", auth=requests.auth.HTTPBasicAuth(app.config.get("DOAJGATE_UN"), app.config.get("DOAJGATE_PW")), verify_ssl=False, port=app.config.get("DOAJGATE_PORT"))


# looks for applications where the provenance dates are later than the last updated dates
# also looks for applications where there is not a corresponding journal
def applications_inconsistencies(outfile_later, outfile_missing, conn):
    with codecs.open(outfile_later, "wb", "utf-8") as f, codecs.open(outfile_missing, "wb", "utf-8") as g:

        out_later = csv.writer(f)
        out_later.writerow(["Application ID", "Application Last Updated", "Latest Provenance Recorded", "Difference"])

        out_missing = UnicodeWriter(g)
        out_missing.writerow(["Application ID", "Application Last Updated", "ISSNs", "Title"])

        counter = 0
        for result in esprit.tasks.scroll(conn, "suggestion", keepalive="45m"):
            counter += 1
            application = Suggestion(**result)
            print counter, application.id

            # Part 1 - later provenance records exist
            latest_prov = Provenance.get_latest_by_resource_id(application.id)
            if latest_prov is not None:
                lustamp = application.last_updated_timestamp
                created = latest_prov.created_date
                pstamp = latest_prov.created_timestamp
                td = pstamp - lustamp
                diff = td.total_seconds()

                thresh = THRESHOLD
                if lustamp < TIMEZONE_CUTOFF:
                    thresh = 3600.0 + THRESHOLD
                    diff = diff - 3600

                if diff > thresh:
                    out_later.writerow([application.id, application.last_updated, created, diff])

            # Part 2 - missing journals
            if application.application_status == "accepted":
                matching_journal = Journal.find_by_issn(application.bibjson().issns())
                if not matching_journal:
                    # Have another go, find by title
                    matching_journal = Journal.find_by_title(application.bibjson().title)
                    if not matching_journal:
                        # No journal found - add it to our list
                        out_missing.writerow([application.id, application.last_manual_update, " ".join(application.bibjson().issns()), application.bibjson().title])

        print "processed", counter, "suggestions"


# looks for journals that were created after the last update on an application, implying the application was not updated
# also looks for missing accounts
def journals_applications_provenance(outfile_applications, outfile_accounts, conn):
    with codecs.open(outfile_applications, "wb", "utf-8") as f, codecs.open(outfile_accounts, "wb", "utf-8") as g:
        out_applications = csv.writer(f)
        out_applications.writerow(["Journal ID", "Journal Created", "Journal Reapplied", "Application ID", "Application Last Updated", "Application Status", "Published Diff", "Latest Edit Recorded", "Latest Accepted Recorded"])

        out_accounts = csv.writer(g)
        out_accounts.writerow(["Journal ID", "Journal Created", "Journal Reapplied", "Missing Account ID"])

        counter = 0
        for result in esprit.tasks.scroll(conn, "journal", keepalive="45m"):
            counter += 1
            journal = Journal(**result)
            print counter, journal.id

            # first figure out if there is a broken related application
            issns = journal.bibjson().issns()
            applications = Suggestion.find_by_issn(issns)
            latest = None
            for application in applications:
                if latest is None:
                    latest = application
                if application.last_updated_timestamp > latest.last_updated_timestamp:
                    latest = application

            if latest is None:
                continue

            jcreated = journal.created_timestamp
            reapp = journal.last_reapplication
            print counter, journal.id, reapp
            if reapp is not None:
                jcreated = datetime.strptime(reapp, "%Y-%m-%dT%H:%M:%SZ")

            lustamp = latest.last_updated_timestamp
            td = jcreated - lustamp
            diff = td.total_seconds()

            thresh = THRESHOLD
            if lustamp < TIMEZONE_CUTOFF:
                thresh = 3600.0 + THRESHOLD
                diff = diff - 3600

            if diff > thresh:
                last_edit = ""
                last_accept = ""

                edit_query = deepcopy(PROV_QUERY)
                edit_query["query"]["bool"]["must"][0]["term"]["resource_id.exact"] = latest.id
                edit_query["query"]["bool"]["must"][1]["term"]["action.exact"] = "edit"
                provs = Provenance.q2obj(q=edit_query)
                if len(provs) > 0:
                    last_edit = provs[0].last_updated

                accept_query = deepcopy(PROV_QUERY)
                accept_query["query"]["bool"]["must"][0]["term"]["resource_id.exact"] = latest.id
                accept_query["query"]["bool"]["must"][1]["term"]["action.exact"] = "status:accepted"
                provs = Provenance.q2obj(q=accept_query)
                if len(provs) > 0:
                    last_accept = provs[0].last_updated

                out_applications.writerow([journal.id, journal.created_date, journal.last_reapplication, latest.id, latest.last_updated, latest.application_status, diff, last_edit, last_accept])

            # now figure out if the account is missing
            owner = journal.owner
            if owner is None:
                out_accounts.writerow([journal.id, journal.created_date, journal.last_reapplication, "NO OWNER"])
            else:
                acc = Account.pull(owner)
                if acc is None:
                    out_accounts.writerow([journal.id, journal.created_date, journal.last_reapplication, owner])

        print "processed", counter, "journals"


PROV_QUERY = {
    "query": {
        "bool": {
            "must": [
                {"term": {"resource_id.exact": None}},
                {"term": {"action.exact": None}}
            ]
        }
    },
    "sort": [{"created_date": {"order": "desc"}}]
}

if __name__ == "__main__":
    print 'Starting {0}.'.format(datetime.now())
    applications_inconsistencies("apps_with_prov.csv", "apps_accepted_without_journals.csv", local)
    journals_applications_provenance("journals_applications_provenance.csv", "journals_no_accounts.csv", local)
    print 'Finished {0}.'.format(datetime.now())
