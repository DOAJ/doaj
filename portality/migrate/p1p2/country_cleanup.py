import sys
from datetime import datetime

from portality import models
from portality import xwalk

def main(argv=sys.argv)
    start = datetime.now()
    
    journal_iterator = models.Journal.all_in_doaj()
    
    counter = 0
    for j in journal_iterator:
        counter += 1
        j.bibjson().country = xwalk.get_country_code(j.bibjson().country)
        j.prep()
        j.save()
    
    end = datetime.now()
    
    print "Updated Journals", counter
    print start, end
    print 'Time taken:', end-start

if __name__ == '__main__':
    main()
