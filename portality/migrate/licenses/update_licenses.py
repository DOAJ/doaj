from esprit import raw
from portality import models

"""
Use a scroll search to update mis-labelled licenses in the DOAJ.
Requires esprit (
"""

license_correct_dict = { "CC by" : "CC BY",
                         "CC by-nc" : "CC BY-NC",
                         "CC by-nc-nd" : "CC BY-NC-ND",
                         "CC by-nc-sa" : "CC BY-NC-SA",
                         "CC-BY-NC-SA" : "CC BY-NC-SA",
                         "CC by-sa" : "CC BY-SA",
                         "CC by-nd" : "CC BY-ND",
                         "not-cc-like" : "Not CC-like"
                        }

# Connection to the ES index
conn = raw.make_connection(None, 'localhost', 9200, 'doaj')

# Initialise the search and get our first batch of results
resp = raw.initialise_scroll(conn, type='article', query=None, keepalive='1m')

articles = raw.unpack_result(resp)

print "Articles"
for i in articles:
    try:
        print "index\t{0}".format(i['index']['license'])
        print "bibjson\t{0}".format(i['bibjson']['journal']['license'])
    except:
        print "no license"


print "\nJournals"
resp2 = raw.initialise_scroll(conn, type='journal')
journals = raw.unpack_result(resp2)

for j in journals:
    try:
        print "index\t{0}".format(j['index']['license'])
        print "bibjson\t{0}".format(j['bibjson']['license'])
    except:
        print "no license"

# Following that, use the following scructure:
"""
# Scroll search through the index and correct according to the above dict
batch = []
batch_size = 1000
for acc in models.Account.iterall(page_size=10000): # Change to esprit search (on articles)
    journals = acc.journal
    if journals is not None and len(journals) > 0:
        for j in journals:
            record = models.Journal.pull(j)
            if record.owner is None:
                record.set_owner(acc.id)
                batch.append(record.data)

    if len(batch) >= batch_size:
        print "writing ", len(batch)
        models.Journal.bulk(batch)
        batch = []

if len(batch) > 0:
    print "writing ", len(batch)
    models.Journal.bulk(batch)

"""
