from portality import constants
from portality.models import Journal, Application
from portality.ui.messages import Messages


def set_date_applied(journal: Journal):
    """
    Set the date_applied field on the related applications of the journal
    :param journal: The journal to update
    :return: None
    """
    related_applications = journal.related_applications_ordered
    if related_applications is None or len(related_applications) == 0:
        return journal

    app_id = related_applications[-1].get("application_id")
    app = Application.pull(app_id)
    if app is None:
        return journal

    applied = app.date_applied
    if not applied:
        return journal

    journal.date_applied = applied
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