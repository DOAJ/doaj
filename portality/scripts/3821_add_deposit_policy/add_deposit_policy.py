"""
The CSV contains a list of journals; some of them are indexed DOAJ. Updates the author repository policy answers for those that are indexed.

* identify the journals from the list that are indexed in DOAJ
* update the repository policy questions with the new answer: Mir@bel, plus URL
* don't change the manual last updated date
* output a list of journals updated successfully

"""

import csv
from copy import deepcopy

from portality.models import Journal


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("--save", help="Apply the changes to the Journal record", action='store_true')
    args = parser.parse_args()

    print(args.save)

    with open('Mirabel-deposit-policy.csv', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        with open('add-Mirabel-deposit-policy.csv', 'w') as g:
            writer = csv.DictWriter(g, fieldnames=list(reader.fieldnames) + ['found', 'existing deposit policy',
                                                                             'existing deposit policy url', 'added'])
            writer.writeheader()

            for r in reader:
                pissn = r.get('Journal ISSN (print version)', None)
                eissn = r.get('Journal EISSN (online version)', None)

                s = deepcopy(r)

                try:
                    j = Journal.find_by_issn_exact([pissn, eissn])[0]
                    s['found'] = j.id
                    s['existing deposit policy'] = j.bibjson().deposit_policy
                    s['existing deposit policy url'] = j.bibjson().deposit_policy_url

                    if args.save:
                        # Do deposit update
                        dp = r.get('Deposit policy directory')
                        if dp not in j.bibjson().deposit_policy:
                            j.bibjson().add_deposit_policy(r.get('Deposit policy directory'))
                        j.bibjson().deposit_policy_url = r.get('URL for deposit policy')

                        j.prep()
                        j.save(blocking=True)
                        s['added'] = 'y'

                except IndexError:
                    pass   # Nothing to do, it's not in the DOAJ index

                writer.writerow(s)
