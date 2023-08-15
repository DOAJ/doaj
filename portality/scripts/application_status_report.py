from portality import models
import csv

"""This script generates a report of the status of applications in the DOAJ. The output is a CSV file with number
    of applications in each status(new, accepted, rejected) for each year."""


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
          }
        }


def status_query(date_year_from, date_year_to, resource_id, status):
    return {
          "query": {
            "bool": {
              "must": [
                  {
                      "term": {
                          "action": "status:" + status
                      }
                  },
                  {
                  "term": {
                      "resource_id": resource_id
                  }
                },
                {
                  "range": {
                    "created_date": {
                      "gte": str(date_year_from) + "-01-01",
                      "lte": str(date_year_to) + "-12-31"
                    }
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
          "size": 10
        }


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    parser.add_argument("-fy", "--from_year", help="from year to filter by")
    parser.add_argument("-ty", "--to_year", help="to year to filter by")
    args = parser.parse_args()

    if not args.out:
        print("Please specify an output file path with the -o option")

    if not args.from_year:
        print("Please specify a 'from year' to filter the applications with the -fy option")

    if not args.to_year:
        print("Please specify a 'to year' to filter the applications with the -ty option")

    if not args.out or not args.from_year or not args.to_year:
        parser.print_help()
        exit()

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow(["Applications data years", args.from_year + "-" + args.to_year])
        writer.writerow([])

        res = models.Application.query(q=date_applied_query(args.from_year, args.to_year), size=0)
        writer.writerow(["Submitted", res.get("hits", {}).get("total", {}).get("value", 0)])

        accepted_counter = 0
        rejected_counter = 0

        # Application id is saved as resource_id in Provenance model
        # Iterate through all the applications and query Provenance with application id and status to retrieve the
        # status of the applications
        for record in models.Application.iterate(q=date_applied_query(args.from_year, args.to_year), page_size=20):
            accepted_res = models.Provenance.query(
                q=status_query(args.from_year, args.to_year,record["id"], "accepted"), size=0)
            if accepted_res["hits"]["total"]["value"] > 0:
                accepted_counter += 1

            rejected_res = models.Provenance.query(
                q=status_query(args.from_year, args.to_year, record["id"], "rejected"), size=0)
            if rejected_res["hits"]["total"]["value"] > 0:
                rejected_counter += 1

        writer.writerow(["Accepted", accepted_counter])
        writer.writerow(["Rejected", rejected_counter])
