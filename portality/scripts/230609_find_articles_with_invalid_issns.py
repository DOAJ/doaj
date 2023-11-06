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


    with open(args.out+"notfound.csv", "w", encoding="utf-8") as f_notfound, open(args.out+"-identical.csv", "w", encoding="utf-8") as f_identical, open(args.out+"-others.csv", "w", encoding="utf-8") as f_others:
        writer_notfound = csv.writer(f_notfound)
        writer_notfound.writerow(["ID", "PISSN", "EISSN", "Journals found with article's PISSN", "In doaj?",
                         "Journals found with article's EISSN", "In doaj?", "Error"])

        writer_identical = csv.writer(f_identical)
        writer_identical.writerow(["ID", "PISSN", "EISSN", "Journals found with article's PISSN", "In doaj?",
                         "Journals found with article's EISSN", "In doaj?", "Error"])

        writer_others = csv.writer(f_others)
        writer_others.writerow(["ID", "PISSN", "EISSN", "Journals found with article's PISSN", "In doaj?",
                         "Journals found with article's EISSN", "In doaj?", "Error"])

        for a in models.Article.iterate(q=IN_DOAJ, page_size=100, keepalive='5m'):
            article = models.Article(_source=a)
            bibjson = article.bibjson()
            try:
                articlesvc.ArticleService._validate_issns(bibjson)
                articlesvc.ArticleService.match_journal_with_validation(bibjson)
            except exceptions.ArticleNotAcceptable as e:
                id = article.id
                pissn = bibjson.get_identifiers("pissn")
                eissn = bibjson.get_identifiers("eissn")
                j_p = [j["id"] for j in models.Journal.find_by_issn(pissn)]
                j_p_in_doaj = []
                if (j_p):
                    for j in j_p:
                        jobj = models.Journal.pull(j)
                        if (jobj):
                            j_p_in_doaj.append(jobj.is_in_doaj())
                        else:
                            j_p_in_doaj.append("n/a")
                j_e = [j["id"] for j in models.Journal.find_by_issn(eissn)]
                j_e_in_doaj = []
                if (j_e):
                    for j in j_e:
                        jobj = models.Journal.pull(j)
                        if (jobj):
                            j_e_in_doaj.append(jobj.is_in_doaj())
                        else:
                            j_e_in_doaj.append("n/a")
                if (str(e) == "The Print and Online ISSNs supplied are identical. If you supply 2 ISSNs they must be different."):
                    writer_identical.writerow([id, pissn, eissn, j_p, j_p_in_doaj, j_e, j_e_in_doaj, "Identical ISSNs"])
                elif (str(e) == "ISSNs provided don't match any journal."):
                    writer_notfound.writerow([id, pissn, eissn, j_p, j_p_in_doaj, j_e, j_e_in_doaj, "No matching journal found."])
                else:
                    writer_others.writerow([id, pissn, eissn, j_p, j_p_in_doaj, j_e, j_e_in_doaj, str(e)])