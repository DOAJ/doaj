from esprit import tasks, raw
from portality import models

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

out_file = open('rejected_applications', 'w')

# Dump all rejected suggestions to file
tasks.dump(conn, 'suggestion', q=rej_query.copy(), out=out_file)
out_file.close()

# Scroll through all rejected selections, delete all
n_deleted = 0
for s in tasks.scroll(conn, 'suggestion', q=rej_query):

    suggestion_model = models.Suggestion(_source=s)
    suggestion_model.delete()
    n_deleted += 1

print "\n{0} suggestions archived to file and deleted.".format(n_deleted)
