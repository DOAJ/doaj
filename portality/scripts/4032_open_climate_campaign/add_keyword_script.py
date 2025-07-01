import csv
import os

from portality.models import Article

OCC_KEYWORD = "open climate campaign"
ARTICLES_FILE = os.path.join(os.path.dirname(__file__), "ipcc_papers_found.csv")
LOG_FILE = os.path.join(os.path.dirname(__file__), "final_log.log")

def add_occ_keyword(record):
    bib = record.bibjson()
    keywords = bib.keywords
    if OCC_KEYWORD not in keywords:
        bib.add_keyword(OCC_KEYWORD)

    return record

def add_keyword_script():
    with open(ARTICLES_FILE, newline='', encoding='utf-8') as file, \
            open(LOG_FILE, "a", encoding="utf-8") as log:

        reader = csv.DictReader(file)
        for row in reader:
            aid = row.get("article_id")
            a = Article.pull(aid)
            if a.is_in_doaj():
                try:
                    add_occ_keyword(a)
                    a.save()
                    log.write(f'"{OCC_KEYWORD}" added to article {aid}\n')
                except Exception as e:
                    log.write(f'Error processing article {aid}: {str(e)}\n')

if __name__ == "__main__":
    add_keyword_script()
