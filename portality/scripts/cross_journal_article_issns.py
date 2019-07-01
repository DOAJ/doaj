"""
Script which determines which articles have ISSNs which belong to two distinct Journals
"""

from portality import models
from portality.core import app
from portality.clcsv import UnicodeWriter
from datetime import datetime
from portality.lib import dates
import esprit
import codecs


NOT_IN_DOAJ = {
    "query" : {
        "bool" : {
            "must" : [
                {"term" : {"admin.in_doaj" : False}}
            ]
        }
    }
}

if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    args = parser.parse_args()

    if not args.out:
        print "Please specify an output file path with the -o option"
        parser.print_help()
        exit()

    conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])
    total = models.Article.count()

    with codecs.open(args.out, "wb", "utf-8") as f:
        writer = UnicodeWriter(f)
        writer.writerow(["Count", "Article ID", "Article ISSNs", "Match On", "Journal ID", "Journal ISSNs"])

        counter = 1
        sofar = 0
        start = datetime.utcnow()
        for a in esprit.tasks.scroll(conn, models.Article.__type__, page_size=1000, keepalive='5m'):
            sofar += 1
            if sofar % 1000 == 0:
                eta = dates.eta(start, sofar, total)
                print("{now} : {sofar}/{total} | ETA {eta}".format(now=dates.now(), sofar=sofar, total=total, eta=eta))

            article = models.Article(**a)
            bibjson = article.bibjson()
            issns = bibjson.issns()
            if len(issns) == 1:
                continue

            js = models.Journal.find_by_issn(issns, in_doaj=True)

            if len(js) <= 1:
                continue

            for j in js:
                jissns = j.bibjson().issns()
                match_on = list(set(issns) & set(jissns))
                row = [counter, article.id, ", ".join(issns), ", ".join(match_on), j.id, ", ".join(jissns)]
                writer.writerow(row)
                print(row)

            counter += 1



