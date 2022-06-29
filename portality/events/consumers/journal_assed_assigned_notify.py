from flask import url_for

from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.bll import DOAJ
from portality.bll import exceptions


class JournalAssedAssignedNotify(EventConsumer):
    ID = "journal:assed:assigned:notify"

    @classmethod
    def consumes(cls, event):
        return event.id == constants.EVENT_JOURNAL_ASSED_ASSIGNED and \
               event.context.get("journal") is not None

    @classmethod
    def consume(cls, event):
        j_source = event.context.get("journal")

        try:
            journal = models.Journal(**j_source)
        except Exception as e:
            raise exceptions.NoSuchObjectException("Unable to construct Journal from supplied source - data structure validation error, {x}".format(x=e))

        if not journal.editor:
            raise exceptions.NoSuchPropertyException("Journal {x} does not have property `editor`".format(x=journal.id))

        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = journal.editor
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_ASSIGN
        notification.long = svc.long_notification(cls.ID).format(
            journal_name=journal.bibjson().title,
            group_name=journal.editor_group
        )
        notification.short = svc.short_notification(cls.ID)
        notification.action = url_for("editor.journal_page", journal_id=journal.id)

        svc.notify(notification)
