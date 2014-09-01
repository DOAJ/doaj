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

edited = 0
failed = 0
unchanged = 0
nolicence = 0

ed = []
fa = []
un = []
nl = []

# Process the previous set of journals
for j in tasks.scroll(conn, 'journal'):
    try:
        journal_model = models.Journal(_source=j)
        # Change the license
        j_license = journal_model.bibjson().get_license()
        if j_license:
            j_license['type'] = license_correct_dict[j_license['type']]
            j_license['title'] = license_correct_dict[j_license['title']]
            print "edited\t{0}".format(journal_model.id)
            ed.append(journal_model.id)
            edited += 1
            journal_model.prep()
            write_batch.append(journal_model.data)
        else:
            nolicence += 1
            print "no licence\t{0}".format(journal_model.id)
            nl.append(journal_model.id)
    except ValueError:
        print "Failed to create a model"
        print "no model\t{0}".format(journal_model.id)
        failed += 1
        fa.append(journal_model.id)
    except KeyError:
        # No license present, pass
        print "unchanged\t{0}".format(journal_model.id)
        unchanged += 1
        un.append(journal_model.id)
        #pass

    # When we have enough, do some writing
    if len(write_batch) >= batch_size:
        print "writing ", len(write_batch)
        models.Journal.bulk(write_batch)
        write_batch = []

# Write the last part-batch to index
if len(write_batch) > 0:
    print "writing ", len(write_batch)
    models.Journal.bulk(write_batch)

print "\nCompleted. Run scripts/journalinfo.py to update the articles with the new license labels."
print "{0} journals were updated, {1} were left unchanged, {2} had no licence object, and {3} failed.".format(edited, unchanged, nolicence, failed)
