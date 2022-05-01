from flask import url_for

from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.bll import DOAJ
from portality.bll import exceptions


class JournalEditorGroupAssignedNotify(EventConsumer):
    ID = "journal:editor_group:assigned:notify"

    @classmethod
    def consumes(cls, event):
        return event.id == constants.EVENT_JOURNAL_EDITOR_GROUP_ASSIGNED and \
               event.context.get("journal") is not None

    @classmethod
    def consume(cls, event):
        j_source = event.context.get("journal")

        try:
            journal = models.Journal(**j_source)
        except Exception as e:
            raise exceptions.NoSuchObjectException("Unable to construct Journal from supplied source - data structure validation error, {x}".format(x=e))

        if not journal.editor_group:
            return

        editor_group = models.EditorGroup.pull_by_key("name", journal.editor_group)

        if not editor_group.editor:
            raise exceptions.NoSuchPropertyException("Editor Group {x} does not have property `editor`".format(x=editor_group.id))

        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = editor_group.editor
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_ASSIGN

        notification.message = svc.message(cls.ID).format(
            journal_name=journal.bibjson().title
        )
        notification.action = url_for("editor.journal_page", journal_id=journal.id)

        svc.notify(notification)
