"""Edit a field with a scroll search based on a query"""

from esprit import tasks, raw
from portality import models
from portality.core import app

from datetime import datetime

if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print "System is in READ-ONLY mode, script cannot run"
        exit(1)

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-q", "--query", nargs=1, help="A JSON query to provide our results. Required.")
    parser.add_argument("-t", "--type", nargs='+', help="A list of types to edit. Required.")

    args = parser.parse_args()

    if not args.query:
        print 'A query parameter is required. This can be a match_all if you really want to edit indiscriminately.'
        exit(1)

    if not args.type:
        print 'One or more type parameters are required.'
        exit(1)

    start = datetime.now()
    print 'Starting {0}  in 5 seconds, Ctrl+C to exit.'.format(start.isoformat())


'''
Use a scroll search to update a field based on a given query
'''

# Connection to the ES index
conn = raw.make_connection(None, 'localhost', 9200, 'doaj')

write_batch = []
batch_size = 200


def scroll_edit(connection, type, query):

    # Process all journals in the index
    for j in tasks.scroll(connection, type=type, q=query):
        try:
            journal_model = models.Journal(_source=j)
        except ValueError:
            print "Failed to create a model"

        # When we have enough, do some writing
        if len(write_batch) >= batch_size:
            print "writing ", len(write_batch)
            models.Journal.bulk(write_batch)
            write_batch = []

    # Write the last part-batch to index
    if len(write_batch) > 0:
        print "writing ", len(write_batch)
        models.Journal.bulk(write_batch)
