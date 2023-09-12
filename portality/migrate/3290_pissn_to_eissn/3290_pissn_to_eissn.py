"""
A.D. 2022-06-22
Script for issue 3290 - https://github.com/DOAJ/doajPM/issues/3290

* Read in provided CSV
* Extract journal IDs from doaj ToC URL
* Extract journal pISSN from Journal ISSN column
* Compare pissn in our data with the csv for security
* Copy pissn to eissn and clear pissn
* write csv with journal id, old pissn, new pissn (should be empty) and new eissn (should be the same as old pissn) to confirm
"""

import csv

from portality.lib import dates
from portality.models import Journal

if __name__ == '__main__':
    print('Starting {0}.'.format(dates.now()))

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--csv', help='csv containing the journals requiring modifications', required=True)
    parser.add_argument('-o', '--out', help='path to write the output to', required=True)
    args = parser.parse_args()

    with open(args.csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        with open(args.out, 'w', encoding='utf-8') as g:
            new_headers = list(reader.fieldnames) + ['Journal ID', 'old pISSN', 'pISSN', 'eISSN']
            writer = csv.DictWriter(g, new_headers)
            writer.writeheader()

            for row in reader:
                j_id = row['URL in DOAJ'].split('/').pop()
                pissn_csv = row['Journal ISSN (print version)']
                try:
                    j = Journal.pull(j_id)
                    jbib = j.bibjson()
                    pissn = jbib.pissn
                    if pissn != pissn_csv:
                        row.update({'Journal ID': j_id, 'pISSN': "journal pissn does not match the csv", 'eISSN': 'skipped'})
                    else:
                        jbib.eissn = pissn
                        del j.bibjson().pissn
                        j.save()
                        row.update(
                            {'Journal ID': j_id, 'old pISSN': pissn, 'pISSN': jbib.pissn, 'eISSN': jbib.eissn})

                except AttributeError as e:
                    # else we haven't found the owner at all
                    row.update({'Journal ID': j_id, 'old pISSN': pissn, 'pISSN': str(e), 'eISSN': 'skipped'})

                writer.writerow(row)

    print('Finished {0}.'.format(dates.now()))
