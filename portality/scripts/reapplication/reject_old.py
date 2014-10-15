from esprit import tasks, raw
from portality import models, settings
from datetime import datetime

'''Reject all applications with created_date prior to 19 March 2014, add note to explain.'''

APPLICATION_NOTE = "Application invalid. Automatically rejected as this was received before the new Application Form was launched. This note has been automatically generated."

# Connection to the ES index
conn = raw.make_connection(None, 'localhost', 9200, 'doaj')

batch_size = 1000
write_batch = []

edited_sug = 0
failed_sug = 0
unchanged_sug = 0

ed_sug = []
fa_sug = []
un_sug = []

# Get the new application threshold from the settings
THRESHOLD_DATE = threshold = datetime.strptime(settings.TICK_THRESHOLD, "%Y-%m-%dT%H:%M:%SZ")

# Scroll through all suggestions
for s in tasks.scroll(conn, 'suggestion'):
    try:
        suggestion_model = models.Suggestion(_source=s)
        # Check the creation date
        cre_date_str = suggestion_model.created_date

        cre_date = datetime.strptime(cre_date_str, "%Y-%m-%dT%H:%M:%SZ")

        if cre_date < THRESHOLD_DATE:
            if suggestion_model.application_status == 'rejected':
                unchanged_sug += 1
                un_sug.append(suggestion_model.id)
            else:
                # If it's older than the threshold, reject it and set a note.
                suggestion_model.set_application_status('rejected')
                suggestion_model.add_note(APPLICATION_NOTE, datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))

                suggestion_model.prep()
                write_batch.append(suggestion_model.data)
                edited_sug += 1
                ed_sug.append(suggestion_model.id)
        else:
            unchanged_sug += 1
            un_sug.append(suggestion_model.id)

    except ValueError:
        print "Failed to create a model"
        print "no model\t{0}".format(suggestion_model.id)
        failed_sug += 1
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

print "{0} suggestions were updated, {1} were left unchanged, and {2} failed.".format(edited_sug, unchanged_sug, failed_sug)

