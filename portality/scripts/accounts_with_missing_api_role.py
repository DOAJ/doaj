"""
This script can be run to generate a CSV output of publisher accounts which do not have th api role set, along
with some useful account information.

```
python accounts_with_missing_api_role.py -o accounts.csv
```
"""
import esprit, codecs
from portality.core import app
from portality.clcsv import UnicodeWriter
from portality import models

MISSING_API_ROLE = {
    "query": {
        "filtered": {
            "query": {
                "term": {
                    "role.exact": "publisher"
                }
            },
            "filter": {
                "not": {
                    "term": {"role.exact": "api"}
                }
            }
        }
    }
}


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    args = parser.parse_args()

    if not args.out:
        print "Please specify an output file path with the -o option"
        parser.print_help()
        exit()

    conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])

    with codecs.open(args.out, "wb", "utf-8") as f:
        writer = UnicodeWriter(f)
        writer.writerow(["ID", "Name", "Email", "Created", "Last Updated"])

        for a in esprit.tasks.scroll(conn, models.Account.__type__, q=MISSING_API_ROLE, page_size=100, keepalive='1m'):
            account = models.Account(_source=a)

            writer.writerow([
                account.id,
                account.name,
                account.email,
                account.created_date,
                account.last_updated
            ])
