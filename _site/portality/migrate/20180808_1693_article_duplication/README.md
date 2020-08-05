# 2018-08-08; Issue 1693 - Article Duplication

This migration covers the deployment of code to bring the article objects in the datastore up to standard
with the structure required for consistent deduplication.

This migration will carry out the following actions:

* regenerate each article's `index` section with their normalised DOI and Fulltext URL


## Execution

    python portality/upgrade.py -u portality/migrate/20180808_1693_article_duplication/migrate.json