# 2018-08-08; Issue 2056 - Keywords should contain only lowercase letters

Migration check all the keywords in database and if they contain any uppercase letters the corresponding journal/article is pulled and its keywords are changed to lowercase.

To run migration simply run:

`python portality/migrate/keywords_no_capital_letters/keywords_capital_letters.py`

No arguments required
