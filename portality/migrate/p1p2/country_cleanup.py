import sys
import os
from datetime import datetime
import csv

from portality import models
from portality import datasets
from portality.lib import dates, paths

OUT_FILENAME = paths.rel2abs(__file__, 'country_cleanup.csv')


def main(argv=sys.argv):
    if len(argv) > 1:
        if argv[1] == '-t':
            test_migration()
        elif argv[1] == '--dry-run':
            migrate(test=True)
        else:
            print('I only understand -t (to test the migration you\'ve run already) or --dry-run (to write out a CSV of what would happen but not change the index) as arguments, .')
    else:
        migrate()


def test_migration():
    data = []
    with open(OUT_FILENAME) as i:
        reader = csv.reader(i)
        for row in reader:
            data.append(row)

    print('Problems:')
    problems = False
    for row in data:
        if row[0] != row[1]:
            problems = True
            print(row[0], ',', row[1])

    if not problems:
        print('No problems')


def migrate(test=False):
    start = dates.now()
    
    journal_iterator = models.Journal.all_in_doaj()
    
    counter = 0
    with open(OUT_FILENAME, 'wb') as o:
        writer = csv.writer(o)
        writer.writerow(['Old country', 'New Country'])

        for j in journal_iterator:
            counter += 1
            oldcountry = j.bibjson().country
            j.bibjson().country = datasets.get_country_code(j.bibjson().country)
            newcountry = j.bibjson().country
            newcountry_name = datasets.get_country_name(newcountry)

            writer.writerow([oldcountry.encode('utf-8'), newcountry_name.encode('utf-8')])

            if not test:
                j.prep()
                j.save()
    
    end = dates.now()
    
    print("Updated Journals", counter)
    print(start, end)
    print('Time taken:', end-start)
    print('You can pass -t to test the migration you just ran.')


if __name__ == '__main__':
    main()
