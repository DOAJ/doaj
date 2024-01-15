from portality import models
from portality.bll.services import article as articlesvc
from portality.bll import exceptions
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
    parser.add_argument("-o", "--out", help="output file path", required=True)
    args = parser.parse_args()


    with open(args.out + "--identical.csv", "w", encoding="utf-8") as f_identical:

        writer_identical = csv.writer(f_identical)
        writer_identical.writerow(["ID", "ISSNs", "Journals found with article's ISSNs", "In doaj?", "Journal's PISSN", "Journal's EISSN"])
        prev_id = "";
        for a in models.Article.iterate(q=IN_DOAJ, page_size=100, keepalive='5m'):
            article = models.Article(_source=a)
            bibjson = article.bibjson()
            try:
                articlesvc.ArticleService._validate_issns(bibjson)
                articlesvc.ArticleService.match_journal_with_validation(bibjson)
            except exceptions.ArticleNotAcceptable as e:
                id = article.id
                issn = bibjson.get_identifiers("pissn")
                journal_info = []
                for j in models.Journal.find_by_issn(issn):
                    jobj = models.Journal.pull(j["id"])
                    if (jobj):
                        jid = j["id"]
                        in_doaj = jobj.is_in_doaj()
                        jbib = jobj.bibjson()
                        jpissn = jbib.pissn
                        jeissn = jbib.eissn
                    else:
                        journal_info.append("n/a")
                    if (str(e) == "The Print and Online ISSNs supplied are identical. If you supply 2 ISSNs they must be different."):
                        writer_identical.writerow([id, issn, jid, in_doaj, jpissn, jeissn])
                    id = "As above";