#!/usr/bin/python
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests


def generate_delete_pattern():
    now = datetime.now()
    delete_month = str(now.month - 3)
    delete_year = str(now.year)
    if len(delete_month) < 2:
        delete_month = '0' + delete_month

    return ".marvel-{0}.{1}*".format(delete_year, delete_month)


def main():
    delete_pattern = generate_delete_pattern()
    print "To delete: {0}".format(delete_pattern)

    if len(delete_pattern) < 8:
        raise PatternDeleteTooShort("Delete pattern too short: {0} , stopping so we don't wipe entire index.".format(delete_pattern))

    r = requests.delete("http://localhost:9200/{0}".format(delete_pattern))
    print 'Delete response status code: {0}'.format(r.status_code)
    print "Delete response text:\n\n{0}".format(r.text)


class PatternDeleteTooShort(Exception):
    pass

if __name__ == '__main__':
    main()
