"""
This script can be run to generate a CSV output of accounts which have marketing consent, along
with their name, email address and date account was created and last updated
```
python accounts_with_marketing_consent.py -o accounts.csv
```
"""

from portality.lib import report_to_csv
from portality import models

WITH_CONSENT = {
    "query": {
        "term": {
            'marketing_consent': True
        }
    }
}

HEADERS = ["ID", "Name", "Email", "Created", "Last Updated", "Updated Since Create?"]


def output_map(acc):
    updated_since_create = acc.created_timestamp < acc.last_updated_timestamp

    return {
        "ID": acc.id,
        "Name": acc.name,
        "Email": acc.email,
        "Created": acc.created_date,
        "Last Updated": acc.last_updated,
        "Updated Since Create?": str(updated_since_create)
    }


def publishers_with_consent(outfile):
    gen = report_to_csv.query_result_generator(WITH_CONSENT, "account", wrap=lambda x: models.Account(**x))
    report_to_csv.report_to_csv(gen, HEADERS, output_map, outfile)


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    args = parser.parse_args()

    if not args.out:
        print "Please specify an output file path with the -o option"
        parser.print_help()
        exit()

    publishers_with_consent(args.out)
