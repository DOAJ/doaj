"""
This script allows you to delete articles in bulk from a query or from a csv.

If you provide a csv, you may also provide a second column containing the delete action, which may be one of:

* delete - actually delete the article
* remove_doi - keep the article, but remove its DOI
* remove_fulltext - keep the article, but remove its Fulltext URLs

"""

from portality import models
import json, codecs, csv
from portality.core import app
from portality import constants

def remove_doi(article_id):
    article = models.Article.pull(article_id)
    article.bibjson().remove_identifiers(idtype=constants.DOI)
    article.save()

def remove_fulltext(article_id):
    article = models.Article.pull(article_id)
    article.bibjson().remove_urls(urltype=constants.FULLTEXT)
    article.save()

if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print "System is in READ-ONLY mode, script cannot run"
        exit()

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-u", "--username", help="username of user whose articles to remove.")
    parser.add_argument("-g", "--ghost", help="specify if you want the articles being deleted not to be snapshot", action="store_true")
    parser.add_argument("-q", "--query", help="file page of json document containing delete-by query")
    parser.add_argument("-ip", "--ignore-paging", help="ignore the from: and size: parameters in a query object", action="store_true")
    parser.add_argument("-c", "--csv", help="csv containing article ids to remove")

    args = parser.parse_args()

    if not args.username and not args.query and not args.csv:
        print "Please specify a username with the -u option, or a query file with the -q option, or a csv with the -c option"
        exit()

    exclusives = 0
    if args.username: exclusives += 1
    if args.query: exclusives += 1
    if args.csv: exclusives += 1

    if exclusives > 1:
        print "You may only specify a username, a query or a csv alone, not combinations."
        exit()

    snapshot = not args.ghost

    if args.username is not None:
        models.Article.delete_selected(owner=args.username, snapshot=snapshot)
        print "Articles deleted"
    elif args.query is not None:
        f = open(args.query)
        query = json.loads(f.read())

        if args.ignore_paging:
            try:
                del query['from']
                del query['size']
            except KeyError:
                pass

        if 'sort' in query:
            print 'You can\'t have "sort" in the query, it breaks ES delete by query. Removing your sort.'
            del query['sort']

        res = models.Article.query(q=query)
        total = res.get("hits", {}).get("total")

        # NOTE: if you have paging, like from: and size: in a query, the
        # hits['total'] will show you all results that match the query,
        # not just the articles that will actually be deleted (which
        # will be just the page of results specified by from: and size:).
        go_on = raw_input("This will delete " + str(total) + " articles.  Are you sure? [Y/N]:")
        if go_on.lower() == "y":
            models.Article.delete_selected(query=query, snapshot=snapshot)
            print "Articles deleted"
        else:
            print "Aborted"
    elif args.csv is not None:
        with codecs.open(args.csv) as f:
            reader = csv.reader(f)
            for row in reader:
                article_id = row[0]
                action = "delete"
                if len(row) > 1:
                    action = row[1]
                if action == "delete":
                    models.Article.remove_by_id(article_id)
                elif action == "remove_doi":
                    remove_doi(article_id)
                elif action == "remove_fulltext":
                    remove_fulltext(article_id)



