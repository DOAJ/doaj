from esprit import raw
from portality import models
import re

'''
Use a scroll search to update mis-labelled licenses in the DOAJ.
Requires esprit (install from https://github.com/richard-jones/esprit)
'''

license_correct_dict = { "CC by" : "CC BY",
                         "CC by-nc" : "CC BY-NC",
                         "CC by-nc-nd" : "CC BY-NC-ND",
                         "CC by-nc-sa" : "CC BY-NC-SA",
                         "CC-BY-NC-SA" : "CC BY-NC-SA",
                         "CC by-sa" : "CC BY-SA",
                         "CC by-nd" : "CC BY-ND",
                         "not-cc-like" : "Not CC-like"
                        }

# Buld a regex to match any of our targets to change, e.g.:
# '\b(not-cc-like|CC by-nc-sa|CC by-nc-nd|CC-BY-NC-SA|CC by-nd|CC by-sa|CC by-nc|CC by)\b'
keys_by_len = sorted(license_correct_dict.keys(), key=len, reverse=True)
match_licenses = re.compile(r'(' + '|'.join(keys_by_len) + r')')

# Method to update the license in the json
def update_license_entry(old_string):
    return match_licenses.sub(lambda x: license_correct_dict[x.group()], old_string)

# Connection to the ES index
conn = raw.make_connection(None, 'localhost', 9200, 'doaj')

# Initialise the search and get our first batch of results
resp = raw.initialise_scroll(conn, type='journal', query=None, keepalive='1m')
journals = raw.unpack_result(resp)

write_batch = []
batch_size = 1000
while journals:

    # Process the previous set of journals
    for j in journals:
        try:
            journal_model = models.Journal(_source=j)
            # Change the license
            j_license = journal_model.bibjson().get_license()
            if j_license:
                # print journal_model.data['bibjson']['license']
                journal_model.data['bibjson']['license'] = update_license_entry(str(j_license))
                write_batch.append(journal_model.data)
        except ValueError:
            print "Failed to create a model"
        except KeyError:
            # No license present, pass
            pass

    if len(write_batch) >= batch_size:
        print "writing ", len(write_batch)
        models.Journal.bulk(write_batch)
        write_batch = []

    # Load the next batch of journals
    try:
        sid = resp.json()['_scroll_id']
        resp = raw.scroll_next(conn, scroll_id=sid)
        journals = raw.unpack_result(resp)
    except ValueError:
        print "Reading JSON failed on: " + resp.text
        print "Aborting"
        break

if len(write_batch) > 0:
    print "writing ", len(write_batch)
    models.Journal.bulk(write_batch)
