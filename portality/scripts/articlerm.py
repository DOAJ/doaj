from portality import models
import json
from portality.core import app

if __name__ == "__main__":
    if app.config.get("READ_ONLY_MODE", False):
        print "System is in READ-ONLY mode, script cannot run"
        exit()

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-u", "--username", help="username of user whose articles to remove.")
    parser.add_argument("-g", "--ghost", help="specify if you want the articles being deleted not to be snapshot", action="store_true")
    parser.add_argument("-q", "--query", help="file page of json document containing delete-by query")

    args = parser.parse_args()

    if not args.username and not args.query:
        print "Please specify a username with the -u option, or a query file with the -q option"
        exit()

    if args.username and args.query:
        print "You can't specify both a username and a query - pick one!"
        exit()

    snapshot = not args.ghost

    if not args.query:
        models.Article.delete_selected(owner=args.username, snapshot=snapshot)
        print "Articles deleted"
    else:
        f = open(args.query)
        query = json.loads(f.read())

        res = models.Article.query(q=query)
        total = res.get("hits", {}).get("total")

        go_on = raw_input("This will delete " + str(total) + " articles.  Are you sure? [Y/N]:")
        if go_on.lower() == "y":
            models.Article.delete_selected(query=query, snapshot=snapshot)
            print "Articles deleted"
        else:
            print "Aborted"



