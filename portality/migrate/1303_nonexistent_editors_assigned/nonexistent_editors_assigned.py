import esprit

from portality.core import app
from portality import models
from portality.lib.dataobj import DataStructureException

'''
Use a scroll search to remove some possible question responses from
applications and journals.
'''

# Connection to the ES index
conn = esprit.raw.Connection(app.config.get("ELASTIC_SEARCH_HOST"), app.config.get("ELASTIC_SEARCH_DB"))


def get_all_valid_editors_usernames():
    return [acc.id for acc in models.Account.q2obj(should_terms={"role": ["admin", "editor", "associate_editor"]}, size=10000)]


def migrate(model, valid_editors):
    edited = False

    if model.editor not in valid_editors:
        model.set_editor('')
        edited = True
        
    return edited

write_batch = []
batch_size = 1000

suggestion_edited_count = 0
suggestion_failed_count = 0
suggestion_unchanged_count = 0

ed_sug = []
fa_sug = []
un_sug = []

valid_editors = get_all_valid_editors_usernames()

# Scroll through all applications
for s in esprit.tasks.scroll(conn, 'suggestion'):
    try:
        suggestion_model = models.Suggestion(_source=s)
        suggestion_edited = migrate(suggestion_model, valid_editors)

        if suggestion_edited:
            ed_sug.append(suggestion_model.id)
            suggestion_edited_count += 1
            write_batch.append(suggestion_model.data)
    except DataStructureException:
        print "Failed to create a model"
        print "no model\t{0}".format(suggestion_model.id)
        suggestion_failed_count += 1
        fa_sug.append(suggestion_model.id)

    # When we have enough, do some writing
    if len(write_batch) >= batch_size:
        print "writing ", len(write_batch)
        models.Suggestion.bulk(write_batch)
        write_batch = []

# Write the last part-batch to index
if len(write_batch) > 0:
    print "writing ", len(write_batch)
    models.Suggestion.bulk(write_batch)

print "{0} suggestions were updated, {1} were left unchanged, {2} failed.".format(suggestion_edited_count, suggestion_unchanged_count, suggestion_failed_count)
