""" Create a CSV of journals last updated before a given date. Headings are:
Journal title
Journal URL
Journal ISSN (print version)
Journal EISSN (online version)
Created date
Owner
Owner's email address
Country
Publisher
"""

import csv

from portality.lib.dates import DEFAULT_TIMESTAMP_VAL
from portality.models import Journal, Account
from portality.core import es_connection
from portality.lib import dates


LAST_MANUAL_UPDATE_BETWEEN = {
    "query": {
        "bool": {
            "filter": {
                "term": {
                    "admin.in_doaj": "true"
                }
            },
            "must": {
                "range": {
                    "last_manual_update": {
                        "gte": "x",
                        "lte": "y"
                    }
                }
            }
        }
    },
    "sort": [
        {
            "created_date": "asc"
        }
    ]
}

if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    parser.add_argument('-s', '--start_date', help=f'Last updated after threshold, default is {DEFAULT_TIMESTAMP_VAL}',
                        default=DEFAULT_TIMESTAMP_VAL)
    parser.add_argument('-e', '--end_date', help='Last updated before threshold, default is now',
                        default=dates.now_str_with_microseconds())
    args = parser.parse_args()

    if not args.out:
        print("Please specify an output file path with the -o option")
        parser.print_help()
        exit()

    conn = es_connection

    # Populate our query
    LAST_MANUAL_UPDATE_BETWEEN['query']['bool']['must']['range']['last_manual_update']["gte"] = args.start_date
    LAST_MANUAL_UPDATE_BETWEEN['query']['bool']['must']['range']['last_manual_update']["lte"] = args.end_date

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID",
                         "Journal Name",
                         "Journal URL",
                         "E-ISSN",
                         "P-ISSN",
                         "Created Date",
                         "Owner",
                         "Owner's email address",
                         "Country",
                         "Publisher"])

        for journal in Journal.iterate(q=LAST_MANUAL_UPDATE_BETWEEN, keepalive='5m', wrap=True):
            bibjson = journal.bibjson()
            index = journal.data["index"]
            owner = journal.owner
            account = Account.pull(owner)

            writer.writerow([journal.id,
                             bibjson.title,
                             bibjson.get_single_url(urltype="homepage"),
                             bibjson.get_one_identifier(bibjson.E_ISSN),
                             bibjson.get_one_identifier(bibjson.P_ISSN),
                             journal.created_date,
                             owner,
                             account.email if account else "Not Found",
                             index["country"],
                             bibjson.publisher
                             ])
