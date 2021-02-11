# 2018-08-08; Issue 2056 - Keywords should contain only lowercase letters

Migration check all the keywords in database and if they contain any uppercase letters the corresponding journal/article is pulled and its keywords are changed to lowercase.

To run migration simply run:

`python portality/upgrade.py -u portality/migrate/20191128_2056_keywords_to_lower/migrate.json

No arguments required
