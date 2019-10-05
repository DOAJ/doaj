from portality import models
from datetime import datetime
""" All this does is scroll through all Journals and run prep(), which includes a check for the tick. """

start = datetime.now()

batch_size = 1000
total = 0

journal_iterator = models.Journal.iterall(page_size=5000)
batch = []
for j in journal_iterator:
    j.prep()
    batch.append(j.data)
    
    if len(batch) >= batch_size:
        total += len(batch)
        print "writing", len(batch), "; total so far", total
        models.Journal.bulk(batch)
        batch = []

if len(batch) > 0:
    total += len(batch)
    print "writing", len(batch), "; total so far", total
    models.Journal.bulk(batch)

end = datetime.now()

print start, "-", end
