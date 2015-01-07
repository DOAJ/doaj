from datetime import datetime
from esprit import tasks, raw
from portality import models

'''Withdraw all journals with incomplete reapplications'''

start = datetime.now()

# Connection to the ES index
conn = raw.make_connection(None, 'localhost', 9200, 'doaj')

withdrawn = []
# Process the previous set of journals
for j in tasks.scroll(conn, 'journal'):
    try:
        journal_model = models.Journal(_source=j)
        linked_reapp = journal_model.current_application
        last_reapp_date = journal_model.last_reapplication

        # If there is a reapplication ID but no last reapplied date
        if linked_reapp and not last_reapp_date:
            # withdraw the journal and its articles from doaj
            journal_model.set_in_doaj(False)
            journal_model.propagate_in_doaj_status_to_articles()

            withdrawn.append(journal_model.id)

    except ValueError:
        print "Failed to create a model. A record is broken."
        break

end = datetime.now()

print "\n{0} journals removed from DOAJ. Their articles were also removed.".format(len(withdrawn))
print start, "-", end

withdrawn.pop()
