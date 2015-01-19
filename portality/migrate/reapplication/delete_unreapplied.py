from esprit import tasks, raw
from portality import models

'''Delete journals and corresponding articles with incomplete reapplications'''

# Connection to the ES index
conn = raw.make_connection(None, 'localhost', 9200, 'doaj')

archv_query = {
            "query" : {
                "term" : {
                    "admin.in_doaj" : "false"
                    }
                }
            }

## Journals ##
json_writer = tasks.JSONListWriter('journals_not_in_doaj.json')

# Dump all journals not in DOAJ to file
tasks.dump(conn, 'journal', q=archv_query.copy(), out=json_writer)
json_writer.close()

# Ask how many journals will be deleted, and delete them.
j_deleted = models.Journal.query(q=archv_query.copy())['hits']['total']
models.Journal.delete_by_query(archv_query)

## Articles ##
json_writer2 = tasks.JSONListWriter('articles_not_in_doaj.json')

# Dump all articles not in DOAJ to file
tasks.dump(conn, 'article', q=archv_query.copy(), out=json_writer2)
json_writer2.close()

# Ask how many articles will be deleted, and delete them.
a_deleted = models.Article.query(q=archv_query.copy())['hits']['total']
models.Article.delete_by_query(archv_query)


print "\n{0} journals archived to file 'journals_not_in_doaj.json' and deleted from index.".format(j_deleted)
print "{0} aricles archived to file 'articles_not_in_doaj.json' and deleted from index.".format(a_deleted)
