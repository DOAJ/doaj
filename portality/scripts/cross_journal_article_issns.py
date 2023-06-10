"""
Script which determines which articles have ISSNs which belong to two distinct Journals
"""

from portality import models
from portality.lib import dates
import codecs
import csv


IN_DOAJ = {
    "query": {
        "bool": {
            "must": [
                {"term": {"admin.in_doaj": True}}
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
        print("Please specify an output file path with the -o option")
        parser.print_help()
        exit()

    total = models.Article.count()

    with codecs.open(args.out, "wb", "utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Count", "Article ID", "Article ISSNs", "Match On", "Journal ID", "Journal ISSNs", "Journal In DOAJ?"])

        counter = 1
        sofar = 0
        start = dates.now()
        for article in models.Article.scroll(q=IN_DOAJ, page_size=1000, keepalive='5m'):
            sofar += 1
            if sofar % 1000 == 0:
                eta = dates.eta(start, sofar, total)
                print("{now} : {sofar}/{total} | ETA {eta}".format(now=dates.now_str(), sofar=sofar, total=total, eta=eta))

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
                row = [counter, article.id, ", ".join(issns), ", ".join(match_on), j.id, ", ".join(jissns), j.is_in_doaj()]
                writer.writerow(row)
                print(row)

            counter += 1
