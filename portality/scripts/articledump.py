from portality import models
import json

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-u", "--username", help="username of user whose articles to export.")
    parser.add_argument("-o", "--out", help="name of output file")

    args = parser.parse_args()

    if not args.username:
        print("Please specify a username with the -u option")
        exit()

    if not args.out:
        print("Please specify and output file with the -o option")
        exit()

    issns = models.Journal.issns_by_owner(args.username)
    articles = models.Article.find_by_issns(issns)

    with open(args.out, "w", encoding="utf8") as f:
        f.write("[")

        first = True
        for article in articles:
            if not first:
                f.write(",")
            else:
                first = False
            data = article.data
            if "index" in data:
                del data["index"]
            f.write(json.dumps(article.data))

        f.write("]")


