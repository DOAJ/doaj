from portality import models
from portality.lib import dates
import csv
import os

"""This script generates a report of the status of applications in the DOAJ. The output is a CSV file with number
    of applications in each status(new, accepted, rejected) for each year."""

# constants
SUBMITTED = "submitted"
ACCEPTED = "accepted"
REJECTED = "rejected"
STATUS_ACCEPTED = "status:accepted"
STATUS_REJECTED = "status:rejected"

DATA = dict()
DEFAULT_COUNTERS = [(SUBMITTED, 0), (ACCEPTED, 0), (REJECTED, 0)]

def date_applied_query(date_year_from, date_year_to,):
    return {
          "query": {
            "bool": {
              "must": [
                {
                  "term": {
                    "admin.application_type.exact": "new_application"
                  }
                },
                {
                  "range": {
                    "admin.date_applied": {
                      "gte": str(date_year_from) + "-01-01",
                      "lte": str(date_year_to) + "-12-31"
                    }
                  }
                }
              ]
            }
          },
          "track_total_hits": True
        }


def status_query(resource_id):
    return {
          "query": {
            "bool": {
              "must": [
                  {
                      "terms": {
                          "action": [STATUS_ACCEPTED, STATUS_REJECTED]
                      }
                  },
                  {
                  "term": {
                      "resource_id": resource_id
                  }
                }
              ]
            }
          },
          "sort": [
            {
                "last_updated": {
                    "order": "desc"
                }
            }
          ],
          "track_total_hits": True
        }

def update_submission_counter(year):
    global DATA
    submission_data = DATA.setdefault(str(year),dict(DEFAULT_COUNTERS))
    submission_data[SUBMITTED] += 1

def update_accepted_counter(year):
    global DATA
    submission_data = DATA.setdefault(str(year), dict(DEFAULT_COUNTERS))
    submission_data[ACCEPTED] += 1

def update_rejected_counter(year):
    global DATA
    submission_data = DATA.setdefault(str(year), dict(DEFAULT_COUNTERS))
    submission_data[REJECTED] += 1

def write_applications_count_to_file(output_dir, from_year, to_year):
    global DATA
    with open(os.path.join(output_dir,"application_status_report" + from_year + "_" + to_year + ".csv"), "w",
              encoding="utf-8") as f:
        writer = csv.writer(f)

        for year, app_data in sorted(DATA.items()):
            writer.writerow(["Year", year])
            writer.writerow([])
            writer.writerow(["Submitted", app_data[SUBMITTED]])
            writer.writerow(["Accepted", app_data[ACCEPTED]])
            writer.writerow(["Rejected", app_data[REJECTED]])
            writer.writerow([])
            writer.writerow([])

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file directory path", required=True)
    parser.add_argument("-fy", "--from_year", help="from-year to filter by", required=True)
    parser.add_argument("-ty", "--to_year", help="to-year to filter by", required=True)
    args = parser.parse_args()


    # Application id is saved as resource_id in Provenance model
    # Iterate through all the applications and query Provenance with application id and status to retrieve the
    # status of the applications
    for record in models.Application.iterate(q=date_applied_query(args.from_year, args.to_year), page_size=20):
        application_year = dates.parse(record["admin"]["date_applied"], dates.FMT_DATETIME_MS_STD).year
        update_submission_counter(application_year)

        provenance_res = models.Provenance.query(q=status_query(record["id"]), size=2)
        if provenance_res["hits"]["total"]["value"] > 0:
            provenance_record = provenance_res["hits"]["hits"][0]["_source"]
            provenance_year = dates.parse(provenance_record["last_updated"], dates.FMT_DATETIME_MS_STD).year
            action_status = provenance_record["action"]

            if action_status == STATUS_ACCEPTED:
                update_accepted_counter(provenance_year)
            elif action_status == STATUS_REJECTED:
                update_rejected_counter(provenance_year)

    write_applications_count_to_file(args.out, args.from_year, args.to_year)
