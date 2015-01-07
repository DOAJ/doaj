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

json_writer = tasks.JSONListWriter('journals_not_reapplied.json')

# Dump all journals not in DOAJ to file
tasks.dump(conn, 'journal', q=archv_query.copy(), out=json_writer)
json_writer.close()

# Ask how many journals will be deleted.
n_deleted = raw.search(conn, 'journal', archv_query).json()['hits']['total']

# Delete all rejected suggestions.
#raw.delete_by_query(conn, 'suggestion', archv_query)

print "\n{0} journals archived to file 'journals_not_reapplied.json' and deleted from index.".format(n_deleted)
