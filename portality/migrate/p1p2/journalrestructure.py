from portality import models

batch_size = 1000
total=0

batch = []
journal_iterator = models.Journal.iterall(page_size=10000)
for j in journal_iterator:
    
    # remove any author-pays stuff
    #if "author_pays" in j.data.get("bibjson"):
    #    del j.data["bibjson"]["author_pays"]
    
    #if "author_pays_url" in j.data.get("bibjson"):
    #    del j.data["bibjson"]["author_pays_url"]
    
    # get rid of all DOAJ subject classifications
    subs = j.bibjson().subjects()
    keep = []
    for sub in subs:
        if sub.get("scheme") == "LCC":
            keep.append(sub)
    j.bibjson().set_subjects(keep)
    
    j.prep()
    batch.append(j.data)
    
    if len(batch) >= batch_size:
        total += len(batch)
        print("writing", len(batch), "; total so far", total)
        models.Journal.bulk(batch)
        batch = []

if len(batch) > 0:
    total += len(batch)
    print("writing", len(batch), "; total so far", total)
    models.Journal.bulk(batch)
