"""
For each article in the DOAJ index:
    * Checks that it has a corresponding journal, deletes it otherwise (if -d set)
    * Ensures that the article in_doaj status is the same as the journal's
    * Applies the journal's information to the article metadata as needed
"""
import esprit
from portality import models
from datetime import datetime
from portality.core import app

batch_size = 1000


def cleanup_articles(allow_deletes=False):

    # Connection to the ES index
    conn = esprit.raw.make_connection(None, 'localhost', 9200, 'doaj')

    write_batch = []
    delete_batch = set()

    # Scroll though all articles in the index
    for a in esprit.tasks.scroll(conn, 'article'):
        try:
            article_model = models.Article(_source=a)
            assoc_journal = article_model.get_journal()
            if assoc_journal is not None:
                # do stuff
                pass
            else:
                delete_batch.add(article_model.id)

        except ValueError:
            # Failed to create model
            continue

        # When we have reached the batch limit, do some writing or deleting
        if len(write_batch) >= batch_size:
            print "writing ", len(write_batch)
            models.Article.bulk(write_batch)
            write_batch = []

        if allow_deletes:
            if len(delete_batch) >= batch_size:
                print "deleting ", len(delete_batch)
                # do deletes
                delete_batch.clear()

    # Finish the last part-batches of writes or deletes
    if len(write_batch) > 0:
        print "writing ", len(write_batch)
        models.Article.bulk(write_batch)
    if allow_deletes:
        if len(delete_batch) > 0:
            print "deleting ", len(delete_batch)
            # do delete
            delete_batch.clear()

if __name__ == "__main__":
    start = datetime.now()
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print "System is in READ-ONLY mode, script cannot run"
        exit()

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--delete", action='store_true', default=False, help="when set, the script will delete articles not in_doaj")
    args = parser.parse_args()

    cleanup_articles(args.delete)

    end = datetime.now()
    print start, "-", end
