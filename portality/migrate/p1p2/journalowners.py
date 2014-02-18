from portality import models

print "Migrating journal owners - adding account ids to journal records"

batch = []
batch_size = 1000
for acc in models.Account.iterall():
    journals = acc.journal
    if journals is not None and len(journals) > 0:
        for j in journals:
            record = models.Journal.pull(j)
            record.set_owner(acc.id)
            batch.append(record.data)
    
    if len(batch) >= batch_size:
        print "writing ", len(batch)
        models.Journal.bulk(batch)
        batch = []

if len(batch) > 0:
    print "writing ", len(batch)
    models.Journal.bulk(batch)
