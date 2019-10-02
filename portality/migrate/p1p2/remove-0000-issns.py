from portality import models

# first thing to do is delete suggestions which are marked "waiting for answer"

q = {
    "query" : {
        "bool" : {
            "must" : [
                {"term" : {"admin.application_status.exact" : "waiting for answer"}}
            ]
        }
    }
}

batch_size = 1000
total=0

batch = []
suggestion_iterator = models.Suggestion.iterall(page_size=10000)
for s in suggestion_iterator:
    
    issns = s.bibjson().get_identifiers(s.bibjson().P_ISSN) + s.bibjson().get_identifiers(s.bibjson().E_ISSN)
    
    delete_0000 = True
    if len(issns) == 1 and issns[0] == '0000-0000':
        print ('suggestion {0} has only 1 id, 0000-0000, not deleting it'.format(s.id))
        delete_0000 = False
    
    if delete_0000:
        s.bibjson().remove_identifiers(id='0000-0000')
        s.prep()
        batch.append(s.data)
    
    if len(batch) >= batch_size:
        total += len(batch)
        print( "writing", len(batch), "; total so far", total)
        models.Suggestion.bulk(batch)
        batch = []

if len(batch) > 0:
    total += len(batch)
    print ("writing", len(batch), "; total so far", total)
    models.Suggestion.bulk(batch)


total = 0
batch = []
journal_iterator = models.Journal.iterall(page_size=10000)
for j in journal_iterator:
    
    issns = j.bibjson().get_identifiers(j.bibjson().P_ISSN) + j.bibjson().get_identifiers(j.bibjson().E_ISSN)
    
    delete_0000 = True
    if len(issns) == 1 and issns[0] == '0000-0000':
        print ('journal {0} has only 1 id, 0000-0000, not deleting it'.format(j.id))
        delete_0000 = False
    
    if delete_0000:
        j.bibjson().remove_identifiers(id='0000-0000')
        j.prep()
        batch.append(j.data)
    
    if len(batch) >= batch_size:
        total += len(batch)
        print ("writing", len(batch), "; total so far", total)
        models.Journal.bulk(batch)
        batch = []

if len(batch) > 0:
    total += len(batch)
    print ("writing", len(batch), "; total so far", total)
    models.Journal.bulk(batch)
