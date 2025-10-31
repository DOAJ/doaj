from portality import constants
from portality.models import Journal, Application
from portality.ui.messages import Messages


def set_date_applied_and_last_full_review(journal: Journal):
    """
    Set the date_applied field on the related applications of the journal,
    and the last full review date.  Rules are as follows:

    * last_full_review is the date_accepted of the oldest related application
    * date_applied is the date_applied of the oldest related application,
      or if that is not available, the created_date of the journal

    :param journal: The journal to update
    :return: None
    """
    related_applications = journal.related_applications_ordered
    if related_applications is None or len(related_applications) == 0:
        return journal

    oldest_app = related_applications[-1]
    first_acceptance = oldest_app.get("date_accepted")
    if first_acceptance:
        journal.last_full_review = first_acceptance

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