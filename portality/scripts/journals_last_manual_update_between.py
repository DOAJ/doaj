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

import esprit
import csv
from portality import models
from portality.core import es_connection
from portality.util import ipt_prefix
from portality.lib import dates


LAST_MANUAL_UPDATE_BETWEEN = {
    "query": {
        "filtered": {
            "query": {"range": {"last_manual_update": {"gte": "", "lte": ""}}},
            "filter": {
                "bool": {
                    "must": {"term": {"in_doaj": "true"}}
                }
            }
        }
    },
    "sort": [{
        "created_date": "asc"
    }]
}

if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    parser.add_argument('-s', '--start_date', help='Last updated after threshold, default is 1970-01-01T00:00:00Z', default='1970-01-01T00:00:00Z')
    parser.add_argument('-e', '--end_date', help='Last updated before threshold, default is now', default=dates.now_with_microseconds())
    args = parser.parse_args()

    if not args.out:
        print("Please specify an output file path with the -o option")
        parser.print_help()
        exit()

    conn = es_connection

    # Populate our query
    LAST_MANUAL_UPDATE_BETWEEN['query']['filtered']['query']['range']['last_manual_update']["gte"] = args.start_date
    LAST_MANUAL_UPDATE_BETWEEN['query']['filtered']['query']['range']['last_manual_update']["lte"] = args.end_date

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

        for j in esprit.tasks.scroll(conn, ipt_prefix(models.Journal.__type__), q=LAST_MANUAL_UPDATE_BETWEEN, limit=800, keepalive='5m'):
            journal = models.Journal(_source=j)
            bibjson = journal.bibjson()
            index = j["index"]
            owner = journal.owner
            account = models.Account.pull(owner)

            writer.writerow([journal.id,
                             bibjson.title,
                             bibjson.get_single_url(urltype="homepage"),
                             bibjson.get_one_identifier(bibjson.E_ISSN),
                             bibjson.get_one_identifier(bibjson.P_ISSN),
                             journal.created_date,
                             owner,
                             account.email,
                             index["country"],
                             bibjson.publisher
                             ])
