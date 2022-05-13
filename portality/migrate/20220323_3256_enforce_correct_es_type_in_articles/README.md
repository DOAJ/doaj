# 2022-03-23, Issue 3256, Articles have been being saved with incorrect es_type

After corresponding changes to the codebase migration simply re-saves all the articles to enforce correct es_type 

To run migration simply run:

`python portality/upgrade.py -u portality/migrate/20220323_3256_enforce_correct_es_type_in_articles/migrate.json

No arguments required
