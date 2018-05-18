"""
Delete the author email field from article records for https://github.com/DOAJ/doajPM/issues/1667
"""

import esprit
from portality.core import app
from portality.models import Article
from datetime import datetime
from operator import delitem


def wipe_emails(connection, batch_size=500):

    batch = []

    for a in esprit.tasks.scroll(connection, 'article', limit=10):
        # Create the article model
        article = Article(**a)
        authors = article.bibjson().author                  # FIXME: this causes a DataStructureException because I've disallowed email in the struct
        [delitem(au, 'email') for au in authors if 'email' in au]
        batch.append(article.data)

        if len(batch) >= batch_size:
            esprit.raw.bulk(connection, 'article', batch, idkey='id')
            batch = []

    # Finish saving the final batch
    esprit.raw.bulk(connection, 'article', batch, idkey='id')


if __name__ == "__main__":
    start = datetime.now()

    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print("System is in READ-ONLY mode, script cannot run")
        exit(1)

    # Connection to the ES index, rely on esprit sorting out the port from the host
    conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])

    # Make sure the user is super serious about doing this.
    resp = raw_input("\nAre you sure? This is a DESTRUCTIVE OPERATION y/N: ")
    if resp.lower() == 'y':
        # Run the function to remove the field
        print("Okay, here we go...")
        wipe_emails(conn)
    else:
        print("Better safe than sorry, exiting.")

    end = datetime.now()
    print(str(start) + "-" + str(end))
