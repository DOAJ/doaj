"""Supply a query to edit all fields based on a regular expression"""
# https://github.com/DOAJ/doaj/issues/1089

from esprit import tasks, raw
from portality.core import app

from datetime import datetime
import json
import re

# Regex to find and replace http for https when it's a hindawi URL
match_hindawi_urls = re.compile(r'http://www.hindawi')
replacement_text = 'https://www.hindawi'


def scroll_edit(connection, es_type, query):
    """ Use a scroll search to update a field based on a given query """
    write_batch = []
    batch_size = 200

    for a in tasks.scroll(connection, type=es_type, q=query):

        # Substitute the text and add to the write batch
        d = match_hindawi_urls.sub(replacement_text, json.dumps(a))
        write_batch.append(json.loads(d))

        # When we have enough, do some writing
        if len(write_batch) >= batch_size:
            print("writing ", len(write_batch))
            raw.bulk(connection, es_type, write_batch)
            write_batch = []

    # Write the last part-batch to index
    if len(write_batch) > 0:
        print("writing ", len(write_batch))
        raw.bulk(connection, es_type, write_batch)


if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print("System is in READ-ONLY mode, script cannot run")
        exit(1)

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-q", "--query", help="A JSON query to provide our results. Required.")
    parser.add_argument("-t", "--type", nargs='+', help="A one or more type to edit. Required.")

    args = parser.parse_args()

    if not args.query:
        print('A query parameter is required. This can be a match_all if you really do want to edit indiscriminately.')
        exit(1)

    if not args.type:
        print('One or more type parameters are required. If supplying more than one, ensure the query is valid for both types.')
        exit(1)

    print('Starting {0}.'.format(datetime.now()))

    # Connection to the ES index
    conn = raw.Connection(host=app.config.get("ELASTIC_SEARCH_HOST"), index=app.config.get("ELASTIC_SEARCH_DB"))

    for t in args.type:
        scroll_edit(conn, t, json.loads(args.query))

    print('Finished {0}.'.format(datetime.now()))
