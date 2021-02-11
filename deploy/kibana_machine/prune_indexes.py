#!/usr/bin/python
from datetime import datetime, timedelta
import requests
import re

# TTL in days for monitoring indexes
INDEX_PREFIXES_TTL = {
    '.monitoring': 14,
    'apm': 14,
    'filebeat': 14,
    'metricbeat': 7
}


def generate_deletes(index_list):

    deletes = []
    for idx in index_list:
        for prefix, ttl in INDEX_PREFIXES_TTL.items():
            if idx.startswith(prefix):
                delete_threshold = datetime.now() - timedelta(days=ttl)

                date_part = re.search('(\d+\.?){3}$', idx).group()
                if datetime.strptime(date_part, '%Y.%m.%d') < delete_threshold:
                    deletes.append(idx)

    return deletes


def list_indexes():
    resp = requests.get('http://localhost:9200/_aliases')
    return resp.json().keys()


if __name__ == '__main__':
    index_list = list_indexes()
    delete_pattern = generate_deletes(index_list)
    print('{0} out of {1} to delete:\n{2}\n'.format(len(delete_pattern), len(index_list), delete_pattern))

    for idx in delete_pattern:
        r = requests.delete('http://localhost:9200/{0}'.format(idx))
        print('{0}:\tstatus:\t{1}\t{2}'.format(idx, r.status_code, r.text))
