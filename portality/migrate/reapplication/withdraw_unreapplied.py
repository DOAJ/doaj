from datetime import datetime
from esprit import tasks, raw
from portality import models

'''Withdraw all journals with incomplete reapplications'''

start = datetime.now()

# Connection to the ES index
conn = raw.make_connection(None, 'localhost', 9200, 'doaj')

batch_size = 1000
batch = []

# Process the previous set of journals
for j in tasks.scroll(conn, 'journal'):
    try:
        journal_model = models.Journal(_source=j)
        j_data = journal_model.data
        try:
            j_data['admin']['ticked'] = j_data['ticked']
            del j_data['ticked']
        except:
            no_tick_entry.append(journal_model.id)
        batch.append(j_data)

    except ValueError:
        print "Failed to create a model"

    # When we have enough, do some writing
    if len(batch) >= batch_size:
        print "writing ", len(batch)
        models.Journal.bulk(batch)
        batch = []

# Write the last part-batch to index
if len(batch) > 0:
    print "writing ", len(batch)
    models.Journal.bulk(batch)

end = datetime.now()

print start, "-", end
