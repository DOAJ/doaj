"""
S.E. 2021-11-18
Script for issue 3155 - https://github.com/DOAJ/doajPM/issues/3155

* Read in provided CSV
* Extract journal IDs from doaj ToC URL
* Get owner account for journal
* Add new columns to CSV for account, email address.
"""

import csv

from portality.lib import dates
from portality.models import Journal

if __name__ == '__main__':
    print('Starting {0}.'.format(dates.now()))

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--csv', help='csv containing the journals to add contact details to', required=True)
    parser.add_argument('-o', '--out', help='path to write the output to', required=True)
    args = parser.parse_args()

    with open(args.csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        with open(args.out, 'w', encoding='utf-8') as g:
            new_headers = list(reader.fieldnames) + ['Account ID', 'Account Email']
            writer = csv.DictWriter(g, new_headers)
            writer.writeheader()

            for row in reader:
                j_id = row['URL in DOAJ'].split('/').pop()
                # Get the Journal and its owner details via the ID
                try:
                    j = Journal.pull(j_id)
                    o = j.owner_account
                    row.update({'Account ID': o.id or '', 'Account Email': o.email or ''})
                except AttributeError:
                    # else we haven't found the owner at all
                    msg = 'ACCOUNT MISSING: ' + j.owner if j else "JOURNAL MISSING"
                    row.update({'Account ID': msg, 'Account Email': ''})

                writer.writerow(row)

    print('Finished {0}.'.format(dates.now()))
