"""
Script which attempts to identify journals, applications and provenance records which show an inconsistent state:

1. All suggestions where there are provenance records from a later time

2. All accepted suggestions where the journal hasn't been created

3. All journals for which the created_date is inconsistent with the application's last_updated date, and for which there are edit and/or accepted provenance records

4. All journals for which the related account is missing

5. All journals which were published earlier than their related application was last updated (suggesting a failure to reapply)
"""

from copy import deepcopy
from datetime import datetime, timedelta

import codecs
import csv
import esprit

from portality import constants
from portality.clcsv import UnicodeWriter
from portality.core import app
from portality.models import Suggestion, Provenance, Journal, Account

APP_TIMEZONE_CUTOFF = datetime.strptime("2017-05-18T14:02:08Z", "%Y-%m-%dT%H:%M:%SZ")
JOURNAL_TIMEZONE_CUTOFF = datetime.strptime("2017-09-21T08:54:05Z", "%Y-%m-%dT%H:%M:%SZ")
THRESHOLD = 20.0

source = {
    "host": app.config.get("ELASTIC_SEARCH_HOST"),
    "index": app.config.get("ELASTIC_SEARCH_DB")
}
local = esprit.raw.Connection(source.get("host"), source.get("index"))

#live = esprit.raw.Connection(app.config.get("DOAJGATE_URL"), "doaj", auth=requests.auth.HTTPBasicAuth(app.config.get("DOAJGATE_UN"), app.config.get("DOAJGATE_PW")), verify_ssl=False, port=app.config.get("DOAJGATE_PORT"))


def adjust_timestamp(stamp, cutoff):
    if stamp < cutoff:
        return stamp + timedelta(seconds=3600)
    return stamp


# looks for applications where the provenance dates are later than the last updated dates
# also looks for applications where there is not a corresponding journal (in_doaj=True)
def applications_inconsistencies(outfile_later, outfile_missing, conn):
    with codecs.open(outfile_later, "wb", "utf-8") as f, codecs.open(outfile_missing, "wb", "utf-8") as g:

        out_later = csv.writer(f)
        out_later.writerow(["Application ID", "Application Last Updated", "Latest Provenance Recorded", "Difference"])

        out_missing = UnicodeWriter(g)
        out_missing.writerow(["Application ID", "Application Last Manual Update", "Latest Provenance Record", "ISSNs", "Title"])

        counter = 0
        for result in esprit.tasks.scroll(conn, "suggestion", keepalive="45m"):
            counter += 1
            application = Suggestion(**result)
            print (counter, application.id)

            # Part 1 - later provenance records exist
            latest_prov = Provenance.get_latest_by_resource_id(application.id)
            if latest_prov is not None:
                lustamp = adjust_timestamp(application.last_updated_timestamp, APP_TIMEZONE_CUTOFF)
                created = latest_prov.created_date
                pstamp = latest_prov.created_timestamp
                td = pstamp - lustamp
                diff = td.total_seconds()

                if diff > THRESHOLD:
                    out_later.writerow([application.id, application.last_updated, created, diff])

            # Part 2 - missing journals
            if application.application_status == constants.APPLICATION_STATUS_ACCEPTED:
                missing = False

                # find the matching journals by issn or by title
                matching_journals = Journal.find_by_issn(application.bibjson().issns())
                if len(matching_journals) == 0:
                    # Have another go, find by title
                    matching_journals = Journal.find_by_title(application.bibjson().title)

                # if there are no matching journals, it is missing.
                if len(matching_journals) == 0:
                    missing = True
                else:
                    # if there are matching journals, find out if any of them are in the doaj.  If none, then journal is still missing
                    those_in_doaj = len([j for j in matching_journals if j.is_in_doaj()])
                    if those_in_doaj == 0:
                        missing = True

                # if the journal is missing, record it
                if missing:
                    created = ""
                    if latest_prov is not None:
                        created = latest_prov.created_date
                    out_missing.writerow([application.id, application.last_manual_update, created, " ".join(application.bibjson().issns()), application.bibjson().title])

        print ("processed", counter, "suggestions")


# looks for journals that were created after the last update on an application, implying the application was not updated
# also looks for missing accounts
# also looks for journals created (or reapplied) significantly before the last manual update on an application
def journals_applications_provenance(outfile_applications, outfile_accounts, outfile_reapps, conn):
    with codecs.open(outfile_applications, "wb", "utf-8") as f, codecs.open(outfile_accounts, "wb", "utf-8") as g, codecs.open(outfile_reapps, "wb", "utf-8") as h:
        out_applications = csv.writer(f)
        out_applications.writerow(["Journal ID", "Journal Created", "Journal Reapplied", "Application ID", "Application Last Updated", "Application Status", "Published Diff", "Latest Edit Recorded", "Latest Accepted Recorded"])

        out_accounts = csv.writer(g)
        out_accounts.writerow(["Journal ID", "Journal Created", "Journal Reapplied", "In DOAJ", "Missing Account ID"])

        out_reapps = csv.writer(h)
        out_reapps.writerow(["Journal ID", "Journal Created", "Journal Reapplied", "Application ID", "Application Created", "Application Last Updated", "Application Last Manual Update", "Application Status", "Published Diff"])

        counter = 0
        for result in esprit.tasks.scroll(conn, "journal", keepalive="45m"):
            counter += 1
            journal = Journal(**result)
            print (counter, journal.id)

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
            reapp = journal.last_update_request
            print (counter, journal.id, reapp)
            if reapp is not None:
                jcreated = datetime.strptime(reapp, "%Y-%m-%dT%H:%M:%SZ")
            jcreated = adjust_timestamp(jcreated, JOURNAL_TIMEZONE_CUTOFF)

            app_lustamp = adjust_timestamp(latest.last_updated_timestamp, APP_TIMEZONE_CUTOFF)
            # app_man_lustamp = latest.last_manual_update_timestamp # no need to adjust this one
            app_man_lustamp = adjust_timestamp(latest.last_manual_update_timestamp, APP_TIMEZONE_CUTOFF)
            td = jcreated - app_lustamp
            mtd = jcreated - app_man_lustamp
            diff = td.total_seconds()
            mdiff = mtd.total_seconds()

            # was the journal created after the application by greater than the threshold?
            if diff > THRESHOLD:
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

                out_applications.writerow([journal.id, journal.created_date, journal.last_update_request, latest.id, latest.last_updated, latest.application_status, diff, last_edit, last_accept])

            # was the journal (in doaj) created before the application by greater than the threshold, and is it in a state other than rejected
            if mdiff < -1 * THRESHOLD and latest.application_status != constants.APPLICATION_STATUS_REJECTED and journal.is_in_doaj():
                out_reapps.writerow([journal.id, journal.created_date, journal.last_update_request, latest.id, latest.created_date, latest.last_updated, latest.last_manual_update, latest.application_status, mdiff])

            # now figure out if the account is missing
            owner = journal.owner
            if owner is None:
                out_accounts.writerow([journal.id, journal.created_date, journal.last_update_request, str(journal.is_in_doaj()), "NO OWNER"])
            else:
                acc = Account.pull(owner)
                if acc is None:
                    out_accounts.writerow([journal.id, journal.created_date, journal.last_update_request, str(journal.is_in_doaj()), owner])

        print ("processed", counter, "journals")


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
    print ('Starting {0}.'.format(datetime.now()))
    applications_inconsistencies("apps_with_prov.csv", "apps_accepted_without_journals.csv", local)
    journals_applications_provenance("journals_applications_provenance.csv", "journals_no_accounts.csv", "journals_reapp_fails.csv", local)
    print ('Finished {0}.'.format(datetime.now()))
