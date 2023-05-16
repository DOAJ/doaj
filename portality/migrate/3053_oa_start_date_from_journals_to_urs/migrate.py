"""
This script finds all journals with existing oa_start date and populates related update requests with the data.

```
python migrate.py -o out.csv
```
"""
import csv
import esprit
from portality.core import es_connection
from portality.lib import dates
from portality.util import ipt_prefix
from portality import models
from datetime import datetime

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

    batch = []
    batch_size = 1000

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "OA Start Date", "Current Application ID", "Application found"])

        for j in esprit.tasks.scroll(conn, ipt_prefix('journal'), q=JOURNALS_WITH_OA_START_DATE, page_size=100, keepalive='1m'):
            journal = models.Journal(_source=j)
            bibjson = journal.bibjson()

            # Propagate OA start date to the update requests we can find
            if journal.current_application is not None:
                ur = models.Application.pull(journal.current_application)
                if ur is not None:
                    application_found = True
                    urb = ur.bibjson()
                    urb.oa_start = bibjson.oa_start

                    batch.append({'doc': ur.data})

                    if len(batch) >= batch_size:
                        print('{0}, writing {1} to {2}'.format(dates.now(), len(batch), ipt_prefix('application')))
                        r = esprit.raw.bulk(es_connection, batch, idkey="doc.id", type_=ipt_prefix("application"),
                                            bulk_type="update")
                        assert r.status_code == 200, r.json()
                        batch = []
                else:
                    application_found = False

                # Write our report
                try:
                    writer.writerow(
                        [journal.id, bibjson.oa_start, journal.current_application, application_found])
                except AttributeError:
                    print("Error reading attributes for journal {0}".format(j['id']))

        if len(batch) > 0:
            print('{0}, final result set / writing {1} to {2}'.format(dates.now(), len(batch),
                                                                      ipt_prefix('application')))
            r = esprit.raw.bulk(es_connection, batch, idkey="doc.id", type_=ipt_prefix("application"),
                                bulk_type="update")
            assert r.status_code == 200, r.json()

