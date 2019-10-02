"""
Delete the author email field from article records for https://github.com/DOAJ/doajPM/issues/1667
"""

import esprit
from portality.core import app
from portality import models
from portality.models import Article
from datetime import datetime

bibjson_struct = models.article.ARTICLE_BIBJSON_EXTENSION
del bibjson_struct['structs']['bibjson']['structs']['author']['fields']['email']

HAS_EMAIL_QUERY = {
    "query": {
        "filtered": {
            "filter": {
                "exists": {"field": "bibjson.author.email"}
            },
            "query": {
                "match_all": {}
            }
        }
    }
}


def wipe_emails(connection, batch_size=500):

    batch = []

    for a in esprit.tasks.scroll(connection, 'article', q=HAS_EMAIL_QUERY):
        # Create the article model
        article = Article(**a)
        # Use the DataObj prune to remove emails
        _ = article.bibjson(construct_silent_prune=True)
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
    resp = input("\nAre you sure? This is a DESTRUCTIVE OPERATION y/N: ")
    if resp.lower() == 'y':
        # Run the function to remove the field
        print("Okay, here we go...")
        wipe_emails(conn)
    else:
        print("Better safe than sorry, exiting.")

    end = datetime.now()
    print(str(start) + "-" + str(end))
