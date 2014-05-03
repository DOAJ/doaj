from portality import models
import json, codecs

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-u", "--username", help="username of user whose articles to remove.")

    args = parser.parse_args()

    if not args.username:
        print "Please specify a username with the -u option"
        exit()

    issns = models.Journal.issns_by_owner(args.username)
    articles = models.Article.find_by_issns(issns)

    for article in articles:
        article.delete()

