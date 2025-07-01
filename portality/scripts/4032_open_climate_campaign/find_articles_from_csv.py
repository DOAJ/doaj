import csv
import os

from portality import models

INPUT_CSV = os.path.join(os.path.dirname(__file__), "IPCC_papers.csv")
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "ipcc_papers_found.csv")

BY_DOI = {
    "query": {
      "bool": {
        "must": [
          { "term": { "bibjson.identifier.type": "doi" }},
          {
            "terms": {
              "bibjson.identifier.id.exact": []
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

    # for doi in dois:
    query = BY_DOI.copy()
    query["query"]["bool"]["must"][1]["terms"]["bibjson.identifier.id.exact"] = dois

    for article in models.Article.scroll(q=query, page_size=100, keepalive='5m'):
        results.append({
            "article_id": article.id,
            "doi_searched": article.get_normalised_doi(),
            "in_doaj": article.is_in_doaj()
        })

    with open(OUTPUT_CSV, "w", newline='', encoding='utf-8') as outfile:
        fieldnames = ["article_id", "doi_searched", "in_doaj"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

if __name__ == "__main__":
    find_articles_from_csv()