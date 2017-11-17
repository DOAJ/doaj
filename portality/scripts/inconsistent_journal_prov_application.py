"""
Script which attempts to identify journals, applications and provenance records which show an inconsistent state:

1. All suggestions where there are provenance records from a later time

2. All journals for which the created_date is inconsistent with the application's last_updated date, and for which there are edit and/or accepted provenance records
"""

from portality.core import app
from portality.models import Suggestion, Provenance, Journal
from portality.models.provenance import ResourceIDQuery
import esprit, codecs, csv, requests
from datetime import datetime
from copy import deepcopy

TIMEZONE_CUTOFF = datetime.strptime("2017-05-18T08:14:46Z", "%Y-%m-%dT%H:%M:%SZ")

source = {
    "host": app.config.get("ELASTIC_SEARCH_HOST"),
    "index": app.config.get("ELASTIC_SEARCH_DB")
}
local = esprit.raw.Connection(source.get("host"), source.get("index"))

# live = esprit.raw.Connection(app.config.get("DOAJGATE_URL"), "doaj", auth=requests.auth.HTTPBasicAuth(app.config.get("DOAJGATE_UN"), app.config.get("DOAJGATE_PW")), verify_ssl=False, port=app.config.get("DOAJGATE_PORT"))

# looks for applications where the provenance dates are later than the last updated dates
def applications_with_later_provenance(outfile, conn):
    with codecs.open(outfile, "wb", "utf-8") as f:
        out = csv.writer(f)
        out.writerow(["Application ID", "Application Last Updated", "Latest Provenance Recorded", "Difference"])

        counter = 0
        for result in esprit.tasks.scroll(conn, "suggestion", keepalive="45m"):
            counter += 1
            application = Suggestion(**result)
            print counter, application.id
            latest_prov = Provenance.get_latest_by_resource_id(application.id)
            #query = ResourceIDQuery(application.id)
            #res = esprit.raw.search(conn, "provenance", query.query())
            #obs = esprit.raw.unpack_result(res)
            #if len(obs) > 0:
            #    latest_prov = Provenance(**obs[0])
            if latest_prov is not None:
                lustamp = application.last_updated_timestamp
                created = latest_prov.created_date
                pstamp = latest_prov.created_timestamp
                td = pstamp - lustamp
                diff = td.total_seconds()
                if diff > 2.0:
                    if lustamp < TIMEZONE_CUTOFF:
                        if diff > 3602.0:
                            out.writerow([application.id, application.last_updated, created, diff])
                    else:
                        out.writerow([application.id, application.last_updated, created, diff])

        print "processed", counter, "suggestions"


# looks for journals that were created after the last update on an application (implying the application was not updated)
def journals_applications_provenance(outfile, conn):
    with codecs.open(outfile, "wb", "utf-8") as f:
        out = csv.writer(f)
        out.writerow(["Journal ID", "Journal Created", "Journal Reapplied", "Application ID", "Application Last Updated", "Application Status", "Published Diff", "Latest Edit Recorded", "Latest Accepted Recorded"])

        counter = 0
        for result in esprit.tasks.scroll(conn, "journal", keepalive="45m"):
            counter += 1
            journal = Journal(**result)
            print counter, journal.id

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

            td = jcreated - latest.last_updated_timestamp
            diff = td.total_seconds()
            if diff > 2.0: # or diff < -2.0:
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

                out.writerow([journal.id, journal.created_date, journal.last_reapplication, latest.id, latest.last_updated, latest.application_status, diff, last_edit, last_accept])

        print "processed", counter, "journals"

PROV_QUERY = {
    "query" : {
        "bool" : {
            "must" : [
                {"term" : {"resource_id.exact" : None}},
                {"term" : {"action.exact" : None}}
            ]
        }
    },
    "sort" : [{"created_date" : {"order" : "desc"}}]
}

if __name__ == "__main__":
    applications_with_later_provenance("apps_with_prov.csv", local)
    journals_applications_provenance("journals_applications_provenance.csv", local)
