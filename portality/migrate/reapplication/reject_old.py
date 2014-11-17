from esprit import tasks, raw
from portality import models
from datetime import datetime
from portality.core import app
import codecs
from portality.clcsv import UnicodeWriter

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


email_list = []
separator_list = [",", "or", "/"]

# Get the new application threshold from the settings
THRESHOLD_DATE = threshold = datetime.strptime(app.config.get("TICK_THRESHOLD", "2014-03-19T00:00:00Z"), "%Y-%m-%dT%H:%M:%SZ")

# Scroll through all suggestions
for s in tasks.scroll(conn, 'suggestion'):
    try:
        suggestion_model = models.Suggestion(_source=s)
        # Check the creation date
        cre_date_str = suggestion_model.created_date

        cre_date = datetime.strptime(cre_date_str, "%Y-%m-%dT%H:%M:%SZ")

        if cre_date < THRESHOLD_DATE:
            if suggestion_model.application_status in ['rejected', "accepted"]:
                unchanged_sug += 1
                un_sug.append(suggestion_model.id)
            else:
                # If it's older than the threshold, reject it, set a note and add the contacts to the csv.

                contact = []
                emails = suggestion_model.get_latest_contact_email()
        
                for sep in separator_list:
                    if isinstance(emails, basestring):
                        if sep in emails:
                            emails = emails.split(sep)

                if isinstance(emails, basestring):
                    contact.append(suggestion_model.get_latest_contact_name())
                    contact.append(emails)
                    contact.append(suggestion_model.bibjson().title)
                    email_list.append(contact)
                else:
                    for e in emails:
                        e = e.strip()
                        contact.append(suggestion_model.get_latest_contact_name())
                        contact.append(e)
                        contact.append(suggestion_model.bibjson().title)
                        email_list.append(contact)
                        contact = []


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


with codecs.open('emails_rejected.csv', 'wb', encoding='utf-8') as csvfile:
    wr_writer = UnicodeWriter(csvfile)
    wr_writer.writerows(email_list)

print "{0} suggestions were updated, {1} were left unchanged, and {2} failed.".format(edited_sug, unchanged_sug, failed_sug)

