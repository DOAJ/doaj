"""
Lookup journal info for a spreadsheet which includes a column of ISSNs of journals not in DOAJ.

https://github.com/DOAJ/doajPM/issues/2329
https://github.com/DOAJ/doajPM/issues/2337
"""

from portality.models import Journal
from portality.clcsv import ClCsv
from copy import deepcopy


def lookup_subject_categories(issns):
    """ By ISSN, get the subject classification of a journal """

    subjects_column = []

    for i in issns:
        il = [s.strip() for s in i.split(',')]
        j = Journal.find_by_issn(il, in_doaj=False)
        if len(j) == 0:
            subjects_column.append('Error: not found')
        elif len(j) == 1:
            subj = j[0].bibjson().subjects()
            subjects_column.append(', '.join([f"{s['scheme']}:{s['code']} - {s['term']}" for s in subj]))
        else:
            subjects_column.append('Error: multiple records found for that ISSN')

    return subjects_column


if __name__ == '__main__':
    # Steps for issue 2337

    csv = ClCsv('/home/cloo/DOAJ_removed_22012020_SuspectedEditorialMisconduct.1.csv')
    heading, issns = csv.get_column('ISSN')

    subjects = lookup_subject_categories(issns)
    newcsv = ClCsv('/home/cloo/DOAJ_removed_22012020_SuspectedEditorialMisconduct.2.csv')
    newcsv.data = deepcopy(csv.data)

    # Add subject data to new CSV as extra column
    newcsv.set_column('Subjects', subjects)
    newcsv.save()
