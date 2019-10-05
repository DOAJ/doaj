from portality import models, settings
import requests, json, time

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

url = settings.ELASTIC_SEARCH_HOST + "/" + settings.ELASTIC_SEARCH_DB + "/suggestion/_query"
resp = requests.delete(url, data=json.dumps(q))

time.sleep(5)

deletable = models.Suggestion.iterate(q, page_size=15000, wrap=False)
for d in deletable:
    id = d.get("id")
    if id is not None:
        models.Suggestion.remove_by_id(id)
        print "removing", id

models.Suggestion.refresh()
time.sleep(10)

batch_size = 1000
total=0

batch = []
suggestion_iterator = models.Suggestion.iterall(page_size=10000)
for s in suggestion_iterator:
    
    # remove any author-pays stuff
    #if "author_pays" in s.data.get("bibjson"):
    #    del s.data["bibjson"]["author_pays"]
    
    #if "author_pays_url" in s.data.get("bibjson"):
    #    del s.data["bibjson"]["author_pays_url"]
    
    # normalise the application statuses
    if s.application_status == "answer received":
        s.set_application_status("in progress")
        
    # remove any EzID from the persistent identifier schemes
    pids = s.bibjson().persistent_identifier_scheme
    if "EzID" in pids:
        i = pids.index("EzID")
        del pids[i]
    s.bibjson().persistent_identifier_scheme = pids
    
    # remove any owner_correspondence
    if "owner_correspondence" in s.data.get("admin", {}):
        del s.data["admin"]["owner_correspondence"]
    
    s.prep()
    batch.append(s.data)
    
    if len(batch) >= batch_size:
        total += len(batch)
        print "writing", len(batch), "; total so far", total
        models.Suggestion.bulk(batch)
        batch = []

if len(batch) > 0:
    total += len(batch)
    print "writing", len(batch), "; total so far", total
    models.Suggestion.bulk(batch)
