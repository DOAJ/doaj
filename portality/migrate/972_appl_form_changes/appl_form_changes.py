import esprit

from portality.core import app
from portality import models
from portality.formcontext.xwalks.interprets import interpret_special

'''
Use a scroll search to remove some possible question responses from
applications and journals.
'''

# Connection to the ES index
conn = esprit.raw.Connection(app.config.get("ELASTIC_SEARCH_HOST"), app.config.get("ELASTIC_SEARCH_DB"))

# Edit the Journals

write_batch = []
batch_size = 1000

journal_edited_count = 0
journal_failed_count = 0
journal_unchanged_count = 0

ed = []
fa = []
un = []

def migrate(model):
    edited = False

    # question 47 - remove the "No" option (my license is not
    # CC-like) and replace with "Publisher's own license" in the
    # Other box.
    lic = model.bibjson().get_license()
    if lic:
        if lic['type'].lower() == 'not cc-like':
            lic['type'] = "Publisher's own license"
            lic['title'] = "Publisher's own license"
            edited = True
    
    # question 51, "With which deposit policy directory does the 
    # journal have a registered deposit policy? *"
    # Here we are removing the OAKlist choice and migrating all those
    #  answers to Sherpa/Romeo, since OAKlist was incorporated into
    # Sherpa/Romeo.
    if 'OAKlist' in model.bibjson().deposit_policy:
        model.bibjson().deposit_policy.remove('OAKlist')
        if 'Sherpa/Romeo' not in model.bibjson().deposit_policy:
            model.bibjson().add_deposit_policy('Sherpa/Romeo')
        edited = True

    # question 52, "Does the journal allow the author(s) to hold the 
    # copyright without restrictions? *"
    # Here we are removing all "Other" answers (i.e. not 
    # straightforward yes/no) by setting them to "No".
    # The .author_copyright['copyright'] field is a string, which can
    #  be: "True", "False", "Whatever the person put in the Other box".
    # If we interpret the string and it remains a string (does not
    # become True or False), then we've got an "Other" answer and must
    # set it to "No"/False.
    if isinstance(
            interpret_special(model.bibjson().author_copyright.get('copyright')),
            str
    ):
        model.bibjson().set_author_copyright(url='', holds_copyright='False')  # it's a string on live at the moment
        edited = True

    # question 54, "Will the journal allow the author(s) to retain 
    # publishing rights without restrictions? *"
    # same deal as question 52 above
    if isinstance(
            interpret_special(
                model.bibjson().author_publishing_rights.get('publishing_rights')
            ),
            str
    ):
        model.bibjson().set_author_publishing_rights(url='', holds_rights='False')  # it's a string on live at the moment
        edited = True
        
    return edited

# Process all journals in the index
for j in esprit.tasks.scroll(conn, 'journal'):
    try:
        journal_model = models.Journal(_source=j)
        journal_edited = migrate(journal_model)

        if journal_edited:
            ed.append(journal_model.id)
            journal_edited_count += 1
            write_batch.append(journal_model.data)
    except ValueError:
        print("Failed to create a model")
        print("no model\t{0}".format(journal_model.id))
        journal_failed_count += 1
        fa.append(journal_model.id)
    except KeyError:
        # No license present
        print("no license information present, unchanged\t{0}".format(journal_model.id))
        journal_unchanged_count += 1
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

suggestion_edited_count = 0
suggestion_failed_count = 0
suggestion_unchanged_count = 0

ed_sug = []
fa_sug = []
un_sug = []

# Scroll through all applications
for s in esprit.tasks.scroll(conn, 'suggestion'):
    try:
        suggestion_model = models.Suggestion(_source=s)
        suggestion_edited = migrate(suggestion_model)

        if suggestion_edited:
            ed_sug.append(suggestion_model.id)
            suggestion_edited_count += 1
            write_batch.append(suggestion_model.data)
    except ValueError:
        print("Failed to create a model")
        print("no model\t{0}".format(suggestion_model.id))
        suggestion_failed_count += 1
        fa_sug.append(suggestion_model.id)
    except KeyError:
        # No license present, pass
        print("no license information present, unchanged\t{0}".format(suggestion_model.id))
        suggestion_unchanged_count += 1
        un_sug.append(suggestion_model.id)

    # When we have enough, do some writing
    if len(write_batch) >= batch_size:
        print("writing ", len(write_batch))
        models.Suggestion.bulk(write_batch)
        write_batch = []

# Write the last part-batch to index
if len(write_batch) > 0:
    print("writing ", len(write_batch))
    models.Suggestion.bulk(write_batch)

print("\nCompleted. Run scripts/journalinfo.py to update the articles with the new license data, and missed_journals.py for the missing journals.")
print("{0} journals were updated, {1} were left unchanged, and {2} failed.".format(journal_edited_count, journal_unchanged_count, journal_failed_count))
print("{0} suggestions were updated, {1} were left unchanged, {2} failed.".format(suggestion_edited_count, suggestion_unchanged_count, suggestion_failed_count))
