#!/usr/bin/python
import requests


def list_indexes():
    resp = requests.get('http://localhost:9200/_aliases')
    return resp.json().keys()


if __name__ == '__main__':
    index_list = list_indexes()
    print('Allowing writes on {0} indexes:\n{1}\n'.format(len(index_list), index_list))

    payload = '{"index.blocks.read_only_allow_delete": null}'
    headers = {'Content-Type': "application/json"}
    for idx in index_list:
        r = requests.put('http://localhost:9200/{0}/_settings'.format(idx), data=payload, headers=headers)
        print('{0}:\tstatus:\t{1}\t{2}'.format(idx, r.status_code, r.text))
