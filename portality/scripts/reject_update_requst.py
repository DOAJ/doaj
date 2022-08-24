from portality.models import Application, Journal
from portality.constants import APPLICATION_STATUS_REJECTED

UR_TO_REJECT = "5742fbfb237f4b38a7b58d54951727d6"
JOURNAL = "56d3896d58c7400eb1fae581ecd2e8d6"

if __name__ == "__main__":
    ur = Application.pull(UR_TO_REJECT)
    j = Journal.pull(JOURNAL)
    ur.set_application_status(APPLICATION_STATUS_REJECTED)
    ur.add_note("This update request has been manually rejected because the journal " + JOURNAL + " is no longer in DOAJ, see: https://github.com/DOAJ/doajPM/issues/3285#issuecomment-1205443986")
    if (ur.current_journal is not None):
        ur.remove_current_journal()
        ur.set_related_journal(JOURNAL)
    if (j.current_application is not None):
        j.remove_current_application()
        j.add_related_application(UR_TO_REJECT)

    ur.save()
    j.save()

