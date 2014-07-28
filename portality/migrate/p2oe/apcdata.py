from portality import models

batch_size = 1000
total=0

batch = []
journal_iterator = models.Journal.iterall(page_size=10000)
for j in journal_iterator:
    bibjson = j.bibjson()
    ap = bibjson.author_pays

    # migrate contiditonal (CON) to yes (Y)
    mod = False
    if ap == "CON":
        mod = True
        bibjson.author_pays = "Y"

    # delete any unknowns
    elif ap == "NY":
        mod = True
        del bibjson.author_pays

    if mod:
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
