from esprit import tasks, raw
from portality import models

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

# Connection to the ES index
conn = raw.make_connection(None, 'localhost', 9200, 'doaj')

write_batch = []
batch_size = 1000

# Process the previous set of journals
for j in tasks.scroll(conn, 'journal'):
    try:
        journal_model = models.Journal(_source=j)
        # Change the license
        j_license = journal_model.bibjson().get_license()
        if j_license:
            j_license['type'] = license_correct_dict[j_license['type']]
            j_license['title'] = license_correct_dict[j_license['title']]
            journal_model.prep()
            write_batch.append(journal_model.data)
    except ValueError:
        print "Failed to create a model"
    except KeyError:
        # No license present, pass
        pass

    # When we have enough, do some writing
    if len(write_batch) >= batch_size:
        print "writing ", len(write_batch)
        models.Journal.bulk(write_batch)
        write_batch = []

# Write the last part-batch to index
if len(write_batch) > 0:
    print "writing ", len(write_batch)
    print models.Journal.bulk(write_batch)

# TODO: update the articles too (they pull the license from the journals)
