#!/usr/bin/python
import requests
from dateutil.relativedelta import relativedelta

from portality.lib import dates


def generate_delete_pattern():
    now = dates.now()
    delete_date = now - relativedelta(months=3)

    return ".marvel-{0}*".format(delete_date.strftime('%Y.%m'))


def main():
    delete_pattern = generate_delete_pattern()
    print("To delete: {0}".format(delete_pattern))

    r = requests.delete("http://localhost:9200/{0}".format(delete_pattern))
    print('Delete response status code: {0}'.format(r.status_code))
    print("Delete response text:\n\n{0}".format(r.text))

if __name__ == '__main__':
    main()
