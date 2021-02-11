from esprit import tasks, raw
from portality import models

'''
Use a scroll search to update mis-labelled licenses in the DOAJ.
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

# Edit the Journals

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

# Process all journals in the index
for j in tasks.scroll(conn, 'journal'):
    try:
        journal_model = models.Journal(_source=j)
        # Change the license
        j_license = journal_model.bibjson().get_license()
        if j_license:
            j_license['type'] = license_correct_dict[j_license['type']]
            j_license['title'] = license_correct_dict[j_license['title']]
            print("edited\t{0}".format(journal_model.id))
            ed.append(journal_model.id)
            edited += 1
            journal_model.prep()
            write_batch.append(journal_model.data)
        else:
            nolicence += 1
            print("no licence\t{0}".format(journal_model.id))
            nl.append(journal_model.id)
    except ValueError:
        print("Failed to create a model")
        print("no model\t{0}".format(journal_model.id))
        failed += 1
        fa.append(journal_model.id)
    except KeyError:
        # No license present
        print("unchanged\t{0}".format(journal_model.id))
        unchanged += 1
        un.append(journal_model.id)

    # When we have enough, do some writing
    if len(write_batch) >= batch_size:
        print("writing ", len(write_batch))
        models.Journal.bulk(write_batch)
        write_batch = []

# Write the last part-batch to index
if len(write_batch) > 0:
    print("writing ", len(write_batch))
    models.Journal.bulk(write_batch)


# Now for Suggestions (applications)
write_batch = []

edited_sug = 0
failed_sug = 0
unchanged_sug = 0
nolicence_sug = 0

ed_sug = []
fa_sug = []
un_sug = []
nl_sug = []

# Scroll through all applications
for s in tasks.scroll(conn, 'suggestion'):
    try:
        suggestion_model = models.Suggestion(_source=s)
        # Change the license
        s_license = suggestion_model.bibjson().get_license()
        if s_license:
            s_license['type'] = license_correct_dict[s_license['type']]
            s_license['title'] = license_correct_dict[s_license['title']]
            print("edited\t{0}".format(suggestion_model.id))
            ed_sug.append(suggestion_model.id)
            edited_sug += 1
            suggestion_model.prep()
            write_batch.append(suggestion_model.data)
        else:
            nolicence_sug += 1
            print("no licence\t{0}".format(suggestion_model.id))
            nl_sug.append(suggestion_model.id)
    except ValueError:
        print("Failed to create a model")
        print("no model\t{0}".format(suggestion_model.id))
        failed_sug += 1
        fa_sug.append(suggestion_model.id)
    except KeyError:
        # No license present, pass
        print("unchanged\t{0}".format(suggestion_model.id))
        unchanged_sug += 1
        un_sug.append(suggestion_model.id)
        #pass

    # When we have enough, do some writing
    if len(write_batch) >= batch_size:
        print("writing ", len(write_batch))
        models.Suggestion.bulk(write_batch)
        write_batch = []

# Write the last part-batch to index
if len(write_batch) > 0:
    print("writing ", len(write_batch))
    models.Suggestion.bulk(write_batch)

print("\nCompleted. Run scripts/journalinfo.py to update the articles with the new license labels, and missed_journals.py for the missing journals.")
print("{0} journals were updated, {1} were left unchanged, {2} had no licence object, and {3} failed.".format(edited, unchanged, nolicence, failed))
print("{0} suggestions were updated, {1} were left unchanged, {2} had no licence object, and {3} failed.".format(edited_sug, unchanged_sug, nolicence_sug, failed_sug))
