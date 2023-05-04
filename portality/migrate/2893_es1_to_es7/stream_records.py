""" Stream all records from an ES 1.7 cluster to a new ES 7.10 cluster """

import elasticsearch
import esprit
from datetime import datetime, timedelta
from portality.core import app, initialise_index
from portality.dao import DomainObject
from portality.lib import dates

# Source                doaj-new-index-1                         doaj-new-index-2
ES_1_HOSTS = [{'host': '10.131.99.251', 'port': 9200}, {'host': '10.131.35.67', 'port': 9200}]
es1 = esprit.raw.Connection(host=ES_1_HOSTS[0]['host'], port=ES_1_HOSTS[0]['port'], index='')

# Destination           doaj-index-1                              doaj-index-2
ES_7_HOSTS = [{'host': '10.131.191.132', 'port': 9200}, {'host': '10.131.191.133', 'port': 9200}]
es7 = elasticsearch.Elasticsearch(ES_7_HOSTS, verify_certs=False)

# Indexes to copy across
INDEXES = [
    'doaj-preserve',
    'doaj-editor_group',
    'doaj-news',
    'doaj-harvester_state',
    'doaj-journal',
    'doaj-article',
    'doaj-lcc',
    'doaj-application',
    'doaj-provenance',
    'doaj-background_job',
    'doaj-account',
    'doaj-bulk_upload',
    'doaj-cache',
    'doaj-upload',
    'doaj-draft_application',
    'doaj-lock']


def prep(es: elasticsearch.Elasticsearch):
    """ Initialise the new cluster """

    print('== Emptying new DOAJ cluster ==')
    print(es.indices.delete('doaj-*')) if es.indices.get('doaj-*') else print('Nothing to do')

    print('== Initialising mappings ==')
    initialise_index(app, es)


def send_batch(batch: list, index_name: str, t_conn: elasticsearch.Elasticsearch):
    """ Make a bulk upload of a singe batch """

    data = ''
    for d in batch:
        data += DomainObject.to_bulk_single_rec(d, idkey='id', action='index')
    return t_conn.bulk(body=data, index=index_name, doc_type=None, refresh=False)


def copy_idx(index_name: str, s_conn: esprit.raw.Connection, t_conn: elasticsearch.Elasticsearch):
    """ Scroll through all records in a given index, issuing bulk uploads to the new cluster """

    print(f'== Copying index {index_name} ==')
    batch = []
    batch_size = 1000
    total = 0
    first_page = esprit.raw.search(s_conn, index_name)
    max = first_page.json().get("hits", {}).get("total", 0)
    type_start = dates.now()

    default_query = {
        "query": {"match_all": {}}
    }

    try:
        for result in esprit.tasks.scroll(s_conn, index_name, q=default_query, keepalive="1m", page_size=1000, scan=True):
            batch.append(result)
            if len(batch) >= batch_size:
                total += len(batch)
                print(dates.now(), f'Writing {len(batch)} to {index_name}; {total} of {max}')
                resp = send_batch(batch, index_name, t_conn)
                print(f'Success: {not resp["errors"]}')

                batch = []
                # do some timing predictions
                batch_tick = dates.now()
                time_so_far = batch_tick - type_start
                seconds_so_far = time_so_far.total_seconds()
                estimated_seconds_remaining = ((seconds_so_far * max) / total) - seconds_so_far
                estimated_finish = batch_tick + timedelta(seconds=estimated_seconds_remaining)
                print(f'Estimated finish time for this type {estimated_finish}.')

    except esprit.tasks.ScrollTimeoutException:
        # Try to write the part-batch to index
        if len(batch) > 0:
            total += len(batch)
            print(dates.now(), f'Scroll timed out / writing {len(batch)} to {index_name}; {total} of {max}')
            resp = send_batch(batch, index_name, t_conn)
            print(f'Success: {not resp["errors"]}')
            batch = []
        else:
            print('Scroll timed out, and nothing to finalise')

    except esprit.tasks.ScrollInitialiseException:
        print("Can't scroll through this index - perhaps missing from this cluster")

    # Write the last part-batch to index
    if len(batch) > 0:
        total += len(batch)
        print(dates.now(), f'final result set / writing {len(batch)} to {index_name}; {total} of {max}')
        resp = send_batch(batch, index_name, t_conn)
        print(f'Success: {not resp["errors"]}')


if __name__ == '__main__':
    prep(es7)
    for i in INDEXES:
        copy_idx(i, es1, es7)
    print('== Done! ==')
