from portality import constants
from portality.models import Journal, Application
from portality.ui.messages import Messages


def set_date_applied_and_last_full_review(journal: Journal):
    """
    Set the date_applied field on the related applications of the journal,
    and the last full review date.  Rules are as follows:

    * last_full_review is the last_manual_update or last_updated date of the journal
    * date_applied is the date_applied of the oldest related application,
      or if that is not available, the created_date of the journal

    :param journal: The journal to update
    :return: None
    """

    lmu = journal.last_manual_update
    if lmu is None or lmu == "1970-01-01T00:00:00Z":
        lmu = journal.last_updated
    journal.last_full_review = lmu

    related_applications = journal.related_applications_ordered
    if related_applications is None or len(related_applications) == 0:
        journal.last_full_review = journal.created_date
        journal.date_applied = journal.created_date
        return journal

    oldest_app = related_applications[-1]
    app_id = oldest_app.get("application_id")
    app = Application.pull(app_id)

    applied_date = journal.created_date
    if app is not None:
        applied_date = app.date_applied
    journal.date_applied = applied_date

    return journal


def set_last_withdrawn(journal: Journal):
    """
    Set the last_withdrawn_date field on the journal if it has been withdrawn
    :param journal: The journal to update
    :return: None
    """
    if journal.is_in_doaj():
        return journal

    lmu = journal.last_manual_update
    if lmu is None or lmu == "1970-01-01T00:00:00Z":
        lmu = journal.last_updated

    issns = [i.lower() for i in journal.bibjson().issns()]
    if "xxxx-xxxx" in issns:
        notes = journal.ordered_notes
        if len(notes) > 0:
            date = notes[0].get("date")
            if date is not None:
                lmu = date

    journal.last_withdrawn = lmu
    journal.add_note(Messages.JOURNAL_WITHDRAWN_NOTE.format(username="unknown user", date=lmu) + " (Last Withdrawn Date inferred during data migration)")
    return journal

def set_date_rejected(application: Application):
    """
    Set the date_rejected field on the related applications of the journal
    :param journal: The journal to update
    :return: None
    """
    if application.application_status != constants.APPLICATION_STATUS_REJECTED:
        return application

    lmu = application.last_manual_update
    if lmu is None or lmu == "1970-01-01T00:00:00Z":
        lmu = application.last_updated

    application.date_rejected = lmu
    application.add_note(f"Date Rejected ({lmu}) inferred during data migration")
    return application