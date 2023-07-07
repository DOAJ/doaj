from portality import models
import csv

"""This script generates a report of the status of applications in the DOAJ. The output is a CSV file with number
    of applications in each status(new, accepted, rejected) for each year."""


def date_applied_query(date_year):
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
                      "gte": str(date_year) + "-01-01",
                      "lte": str(date_year) + "-12-31"
                    }
                  }
                }
              ]
            }
          }
        }


def status_query(date_year, status):
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
                  "range": {
                    "created_date": {
                      "gte": str(date_year) + "-01-01",
                      "lte": str(date_year) + "-12-31"
                    }
                  }
                }
              ]
            }
          }
        }


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    parser.add_argument("-y", "--year", help="year to filter by")
    args = parser.parse_args()

    if not args.out:
        print("Please specify an output file path with the -o option")
        parser.print_help()
        exit()

    if not args.year:
        print("Please specify a year to filter the applications with the -y option")
        parser.print_help()
        exit()

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)

        res = models.Application.query(q=date_applied_query(args.year), size=0)
        writer.writerow(["Submitted", res.get("hits", {}).get("total", {}).get("value", 0)])

        res = models.Provenance.query(q=status_query(args.year, "accepted"), size=0)
        writer.writerow(["Accepted", res.get("hits", {}).get("total", {}).get("value", 0)])

        res = models.Provenance.query(q=status_query(args.year, "rejected"), size=0)
        writer.writerow(["Rejected", res.get("hits", {}).get("total", {}).get("value", 0)])
