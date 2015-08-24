""" Building emails to send asynchronously, via cron job or scheduler """

import from portality import models


def managing_editor_notifications():
    """
    Notify managing editors about two things:
        * Summary of records not touched for X weeks
        * Records marked as ready
    """
    pass


def editor_notifications():
    """ Notify editors how many records are assigned to their group. """

    ed_app_query = {}

    apps = models.Suggestion.query(q=)
    pass


def associate_editor_notifications():
    """
    Notify associates about two things:
        * Records assigned that haven't been updated for X days
        * Record(s) that haven't been updated for Y weeks
    """
    pass



