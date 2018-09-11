"""
This script can be run to generate a CSV output of accounts which have marketing consent, along
with their name, email address and date account was created and last updated
```
python accounts_with_marketing_consent.py -o accounts.csv
```
"""
import esprit, codecs
from portality.core import app
from portality.clcsv import UnicodeWriter
from portality import models

WITH_CONSENT = {
    "query": {
        "term": {
            'marketing_consent': True
        }
    }
}


def publishers_with_consent():
    """ Get accounts for all publishers with journals in the DOAJ """
    for acc in esprit.tasks.scroll(conn, 'account', q=WITH_CONSENT, page_size=100, keepalive='1m'):
        publisher_account = models.Account(**acc)
        yield publisher_account


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
        writer.writerow(["ID", "Name", "Email", "Created", "Last Updated", "Updated Since Create?"])

        for account in publishers_with_consent():

            updated_since_create = account.created_timestamp < account.last_updated_timestamp

            writer.writerow([
                account.id,
                account.name,
                account.email,
                account.created_date,
                account.last_updated,
                updated_since_create
            ])
