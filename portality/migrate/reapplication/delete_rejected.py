from esprit import tasks, raw

'''Delete all rejected applications in DOAJ'''

# Connection to the ES index
conn = raw.make_connection(None, 'localhost', 9200, 'doaj')

rej_query = {
            "query" : {
                "term" : {
                    "admin.application_status.exact" : "rejected"
                    }
                }
            }

json_writer = tasks.JSONListWriter('rejected_applications.json')

# Dump all rejected suggestions to file
tasks.dump(conn, 'suggestion', q=rej_query.copy(), out=json_writer)
json_writer.close()

# Ask how many rejected applications will be deleted.
n_deleted = raw.search(conn, 'suggestion', rej_query).json()['hits']['total']

# Delete all rejected suggestions.
raw.delete_by_query(conn, 'suggestion', rej_query)

print "\n{0} suggestions archived to file 'rejected_applications.json' and deleted from index.".format(n_deleted)
