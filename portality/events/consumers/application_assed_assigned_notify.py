from flask import url_for

from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.bll import DOAJ
from portality.bll import exceptions


class ApplicationAssedAssignedNotify(EventConsumer):
    ID = "application:assed:assigned:notify"

    @classmethod
    def consumes(cls, event):
        return event.id == constants.EVENT_APPLICATION_ASSED_ASSIGNED and \
               event.context.get("application") is not None

    @classmethod
    def consume(cls, event):
        context = event.context
        app_id = context.get("application")
        if app_id is None:
            return
        application = models.Application.pull(app_id)
        if application is None:
            raise exceptions.NoSuchObjectException("No application with id {x} found".format(x=app_id))
        if not application.editor:
            raise exceptions.NoSuchPropertyException("Application {x} does not have property `editor`".format(x=app_id))

        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = application.editor
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_ASSIGN
        notification.message = svc.message(cls.ID).format(
            journal_title=application.bibjson().title,
            group_name=application.editor_group
        )
        notification.action = url_for("editor.application", application_id=app_id)

        svc.notify(notification)