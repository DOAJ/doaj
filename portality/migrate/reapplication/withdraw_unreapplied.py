from datetime import datetime
from portality import models

'''Withdraw all journals with incomplete reapplications'''

start = datetime.now()

withdrawn = []

# Iterate through all journals in the DOAJ
all_journals = models.Journal.all_in_doaj()
for journal_model in all_journals:
    linked_reapp = journal_model.current_application
    last_reapp_date = journal_model.last_reapplication

    # If there is a reapplication ID but no last reapplied date
    if linked_reapp and not last_reapp_date:
        # withdraw the journal and its articles from doaj
        journal_model.set_in_doaj(False)
        journal_model.propagate_in_doaj_status_to_articles()

        withdrawn.append(journal_model.id)

end = datetime.now()

print "\n{0} journals removed from DOAJ. Their articles were also removed.".format(len(withdrawn))
print start, "-", end
