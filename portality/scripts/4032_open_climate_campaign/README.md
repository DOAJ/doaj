# 📄 Script Overview
This project consists of two Python scripts designed to process articles related to the IPCC, following instructions provided in [this GitHub comment (step 1 and 2)](https://github.com/DOAJ/doajPM/issues/4032#issuecomment-2961733603).

## 🔍 Step 1: Find Articles by DOI
Run:

```
python find_articles_from_csv.py
```

This script:

* Reads DOIs from `IPCC_papers.csv` (a renamed file provided by DOAJ).
* Searches for articles by DOI using DOAJ's system.
* Writes matches to `ipcc_papers_found.csv` with the following columns:
  * `article_id`: ID of the found article.
  * `doi_searched`: DOI that was used for the search.
  * `in_doaj`: Whether the article is listed in DOAJ.

## 🏷️ Step 2: Add Keyword to Articles
Run:
```
python add_keyword_script.py
```

This script:

* Reads `article_ids` from `ipcc_papers_found.csv` (output of Step 1).
* For each article that is `in_doaj`:
  * Checks if the `open climate campaign` keyword is already present.
  * If not, adds it to the article record.
* Logs the result in `final_log.log`:
  * If added: `"open climate campaign" added to article <article_id>`
  * If an error occurs: `Error processing article <article_id>: <error_message>`