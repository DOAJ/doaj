#!/usr/bin/python
# Syncs the last 1000 of DOAJ newest records which are not present in the locally
# Usage: ./sync_doaj_records.py source_server_ip destination_server_ip [test] [forever]
# E.g.: ./sync_doaj_records.py 95.85.59.151 95.85.48.213
# IF YOU run this script on doaj-staging, this will copy the newest 1000 records present in yonce to doaj-staging. It checks which ones to copy by querying the destination server's elasticsearch (assumed port 9200) and calculating which ones from the source are not present in there.
# Append "test" to the arguments to test the process first, see how many records would go into ES without actually putting them in
# Append "forever" to the arguments to keep syncing records forever. Useful during a server move..

# The script will sync all DOAJ objects in all types defined in portality.settings.MAPPINGS .


# Again, this script calculates which records needs to be synced from 2
# ES endpoints, but it will WRITE TO the elasticsearch instance defined
# in the application config!
import requests
import sys
import json
import time
from portality.core import app
config = app.config

ENDPOINT_TEMPLATE = "http://{server}:9200/doaj/{type}/_search?q=*&size=1000&sort=created_date:desc"


def abort(msg):
    raise Exception(msg)


def sync_type(es_type, source_server, destination_server, testing):
    src = ENDPOINT_TEMPLATE.format(server=source_server, type=es_type)
    dst = ENDPOINT_TEMPLATE.format(server=destination_server, type=es_type)

    source_data = requests.get(src).text
    dest_data = requests.get(dst).text

    s = json.loads(source_data)
    d = json.loads(dest_data)

    try:
        s_total = s['hits']['total']
        s = s['hits']['hits']
    except KeyError:
        print('Skipping', es_type, 'does not have created_date in its mapping. Probably 0 documents, so no mapping beyond the dynamic template has been created, so no point in syncing this type anyway.')
        return

    d_total = d['hits']['total']
    d = d['hits']['hits']

    if s_total < d_total:
        abort("Source has less docs than destination, aborting since your source and destination could be completely out of sync (both have docs than the other one does not). Investigate, fix and rerun.")

    removed = 0
    for s_hit in s[:]:
        for d_hit in d:
            if s_hit["_id"] == d_hit["_id"]:
                removed += 1
                s.remove(s_hit)

    print('Putting', len(s), 'newest records into ES.')
    # print 'You have 5 seconds to terminate this script with Ctrl+C if the number seems off.'
    # time.sleep(5)

    for diff in s:
        if testing:
            print('TESTING - would PUT', diff['_id'])
        else:
            r = requests.put(
                '{es_host}/{es_index}/{es_type}/{rec_id}'.format(es_host=config['ELASTIC_SEARCH_HOST'], es_index=config['ELASTIC_SEARCH_DB'], es_type=es_type, rec_id=diff['_id']),
                data=json.dumps(diff['_source'])
            )
            print(diff['_id'], r.status_code)
            if r.status_code not in [200, 201]:
                print('ES error for record', diff['_id'], 'HTTP status code:', r.status_code)

    #print 'PUT', len(s), 'newest records into ES.'


def main(argv=None):
    if not argv:
        argv = sys.argv

    # TODO use argparse and remove this terrible mess
    source_server = argv[1]
    destination_server = argv[2]

    testing = False
    if len(argv) > 3:
        if argv[3] == 'test':
            testing = True

    forever = False
    if len(argv) > 3:
        if argv[3] == 'forever':
            forever = True
    if len(argv) > 4:
        if argv[4] == 'forever':
            forever = True

    if forever:
        while True:
            for es_type in config['MAPPINGS']:
                sync_type(es_type, source_server, destination_server, testing=testing)
    else:
        for es_type in config['MAPPINGS']:
            sync_type(es_type, source_server, destination_server, testing=testing)


if __name__ == '__main__':
    main()
