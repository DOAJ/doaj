import csv
import os

from portality import models
from portality.lib import normalise

INPUT_CSV = os.path.join(os.path.dirname(__file__), "IPCC_papers.csv")
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "ipcc_papers_found.csv")

BY_DOI = {
    "query": {
      "bool": {
        "must": [
          {
            "term": {
              "index.doi.exact": ""
            }
          }
        ]
      }
    }
  }


def find_articles_from_csv():
    dois = []
    with open(INPUT_CSV, newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            doi = row.get("doi")
            if doi:
                dois.append(doi)
    
    results = []

    for doi in dois:
        ndoi = normalise.normalise_doi(doi)
        query = BY_DOI.copy()
        query["query"]["bool"]["must"][0]["term"]["index.doi.exact"] = ndoi
        found = False
        articles = models.Article.object_query(query)
        if articles:
            article = articles[0]
            results.append({
                "article_id": article.id,
                "supplied_doi": doi,
                "doi_searched": ndoi,
                "article_normalised_doi": article.get_normalised_doi(),
                "in_doaj": article.is_in_doaj()
            })
            found = True
        if not found:
            results.append({
                "article_id": "",
                "supplied_doi": doi,
                "doi_searched": ndoi,
                "article_normalised_doi": "",
                "in_doaj": ""
            })

    with open(OUTPUT_CSV, "w", newline='', encoding='utf-8') as outfile:
        fieldnames = ["article_id", "supplied_doi", "doi_searched", "article_normalised_doi", "in_doaj"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

if __name__ == "__main__":
    find_articles_from_csv()