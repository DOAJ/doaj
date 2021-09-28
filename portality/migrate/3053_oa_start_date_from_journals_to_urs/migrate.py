"""
This script can be run to generate a CSV output of accounts which do not have their passwords set, along
with some useful account information, and possible explanations for the lack of password

```
python accounts_with_missing_passwords.py -o accounts.csv
```
"""
import csv
import esprit
from portality.core import es_connection
from portality.util import ipt_prefix
from portality import models

JOURNALS_WITH_OA_START_DATE = {
    "query": {
        "filtered": {
            "filter": {
                "exists" : {
                    "field" : "bibjson.oa_start"
                }
            },
            "query": {
                "match_all": {}
            }
        }
    },
    "size": 200000
}


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    args = parser.parse_args()

    if not args.out:
        print("Please specify an output file path with the -o option")
        parser.print_help()
        exit()

    conn = es_connection

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "OA Start Date", "Current Application ID", "Application found"])

        for j in esprit.tasks.scroll(conn, ipt_prefix('journal'),
                                     q=JOURNALS_WITH_OA_START_DATE,
                                     page_size=100, keepalive='1m'):

            journal = models.Journal(_source=j)
            bibjson = journal.bibjson()
            if journal.current_application is not None:
                ur = models.Application.pull(journal.current_application)
                application_found = True
                if ur is not None:
                    application_found = False
                    urb = ur.bibjson()
                    urb.oa_start = bibjson.oa_start
                    ur.save()

                try:
                    writer.writerow(
                        [journal.id, bibjson.oa_start, journal.current_application, application_found])
                except AttributeError:
                    print("Error reading attributes for journal {0}".format(j['id']))

