""" Scroll through articles, removing duplicate subjects. No evidence of same in journals """

import esprit
import json
from portality import models
from datetime import datetime
from portality.core import app
from portality.util import unicode_dict

batch_size = 1000

# A list of articles we have failed to create models for
failed_articles = []


def rem_dup_sub(conn, write_changes=False):

    write_batch = []
    updated_count = 0
    same_count = 0

    # Scroll though all articles in the index
    for a in esprit.tasks.scroll(conn, 'article', page_size=100, keepalive='5m'):
        try:
            article_model = models.Article(_source=a)

            # Remove the duplicates
            subjects = unicode_dict(article_model.bibjson().subjects())
            newsub = []

            for sub in subjects:
                if sub not in newsub:
                    newsub.append(sub)

            if newsub != subjects:
                updated_count += 1
                if write_changes:
                    article_model.data['bibjson']['subject'] = newsub
                    article_model.prep()
                    write_batch.append(article_model.data)
            else:
                same_count += 1

        except ValueError:
            # Failed to create model (this shouldn't happen!)
            failed_articles.append(json.dumps(a))
            continue

        # When we have reached the batch limit, do some writing or deleting
        if len(write_batch) >= batch_size:
            print("writing ", len(write_batch))
            models.Article.bulk(write_batch)
            write_batch = []

    # Finish the last part-batches of writes
    if len(write_batch) > 0:
        print("writing ", len(write_batch))
        models.Article.bulk(write_batch)

    return updated_count, same_count


if __name__ == "__main__":
    start = datetime.now()

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-w",
                        "--write",
                        action='store_true',
                        default=False,
                        help="when set, the script will write changes to the index")
    args = parser.parse_args()

    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print("System is in READ-ONLY mode, enforcing read-only for this script")
        args.write = False

    # Connection to the ES index, rely on esprit sorting out the port from the host
    conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])

    (u, s) = rem_dup_sub(conn, args.write)

    if args.write:
        print("Done. {0} articles updated, {1} remain unchanged.".format(u, s))
    else:
        print("Not written. {0} articles to be updated, {1} to remain unchanged. Set -w to write changes.".format(u, s))

    if len(failed_articles) > 0:
        print("Failed to create models for some articles in the index. Something is quite wrong.")
        for f in failed_articles:
            print(f)

    end = datetime.now()
    print(start, "-", end)
