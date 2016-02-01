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

# Cache the Journals here, so we don't keep searching for them in the index
journal_cache = {}


def cleanup_articles(write_changes=False):

    # Connection to the ES index
    conn = esprit.raw.make_connection(None, 'localhost', 9200, 'doaj')

    write_batch = []
    delete_batch = set()

    updated_count = 0
    same_count = 0
    deleted_count = 0

    # Scroll though all articles in the index
    for a in esprit.tasks.scroll(conn, 'article'):
        try:
            article_model = models.Article(_source=a)

            # Try to find journal in our cache
            bibjson = article_model.bibjson()
            pissns = bibjson.get_identifiers(bibjson.P_ISSN)
            eissns = bibjson.get_identifiers(bibjson.E_ISSN)
            allissns = list(set(pissns + eissns))

            assoc_journal = None
            for issn in allissns:
                try:
                    assoc_journal = journal_cache[issn]
                    break
                except KeyError:
                    continue

            # Cache miss; ask the article model to try to find its journal
            if assoc_journal is None:
                assoc_journal = article_model.get_journal()

                # Add the newly found journal to our cache
                if assoc_journal is not None:
                    for issn in allissns:
                        journal_cache[issn] = assoc_journal

            # By the time we get to here, we still might not have a Journal, but we tried.
            if assoc_journal is not None:
                # Track changes, write only if different
                old = article_model.data.copy()

                # Update the article's metadata, including in_doaj status
                article_model.add_journal_metadata(assoc_journal)
                new = article_model.data
                if new == old:
                    same_count += 1
                else:
                    updated_count += 1
                    if write_changes:
                        article_model.prep()
                        write_batch.append(article_model.data)

            else:
                # This article's Journal is no-more, or has evaded us; we delete the article.
                deleted_count += 1
                if write_changes:
                    delete_batch.add(article_model.id)

        except ValueError:
            # Failed to create model (this shouldn't happen!)
            continue

        # When we have reached the batch limit, do some writing or deleting
        if len(write_batch) >= batch_size:
            print "writing ", len(write_batch)
            models.Article.bulk(write_batch)
            write_batch = []

        if len(delete_batch) >= batch_size:
            print "deleting ", len(delete_batch)
            esprit.raw.bulk_delete(conn, 'article', delete_batch)
            delete_batch.clear()

    # Finish the last part-batches of writes or deletes
    if len(write_batch) > 0:
        print "writing ", len(write_batch)
        models.Article.bulk(write_batch)
    if len(delete_batch) > 0:
        print "deleting ", len(delete_batch)
        esprit.raw.bulk_delete(conn, 'article', delete_batch)
        delete_batch.clear()

    return updated_count, same_count, deleted_count

if __name__ == "__main__":
    start = datetime.now()

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--write", action='store_true', default=False, help="when set, the script will write changes to the index")
    args = parser.parse_args()

    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print "System is in READ-ONLY mode, enforcing read-only for this script"
        args.write = False

    (u, s, d) = cleanup_articles(args.write)

    if args.write:
        print "Done. {0} articles updated, {1} remain unchanged, and {2} deleted.".format(u, s, d)
    else:
        print "Changes not written to index. {0} articles to be updated, {1} to remain unchanged, and {2} to be deleted. Set -w to write changes.".format(u, s, d)

    end = datetime.now()
    print start, "-", end
