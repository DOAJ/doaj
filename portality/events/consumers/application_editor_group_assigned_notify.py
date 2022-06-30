from flask import url_for

from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.bll import DOAJ
from portality.bll import exceptions


class ApplicationEditorGroupAssignedNotify(EventConsumer):
    ID = "application:editor_group:assigned:notify"

    @classmethod
    def consumes(cls, event):
        return event.id == constants.EVENT_APPLICATION_EDITOR_GROUP_ASSIGNED and \
               event.context.get("application") is not None

    @classmethod
    def consume(cls, event):
        app_source = event.context.get("application")

        try:
            application = models.Application(**app_source)
        except Exception as e:
            raise exceptions.NoSuchObjectException("Unable to construct Application from supplied source - data structure validation error, {x}".format(x=e))

        if not application.editor_group:
            return

        editor_group = models.EditorGroup.pull_by_key("name", application.editor_group)

        if not editor_group.editor:
            raise exceptions.NoSuchPropertyException("Editor Group {x} does not have property `editor`".format(x=editor_group.id))

        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = editor_group.editor
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_ASSIGN

        notification.long = svc.long_notification(cls.ID).format(
            journal_name=application.bibjson().title
        )
        notification.short = svc.short_notification(cls.ID)

        notification.action = url_for("editor.application", application_id=application.id)

        svc.notify(notification)
