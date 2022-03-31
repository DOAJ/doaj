from flask import url_for

from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.lib import edges
from portality.bll import DOAJ


class ApplicationAssedInprogressNotify(EventConsumer):
    ID = "application:assed:inprogress:notify"

    @classmethod
    def consumes(cls, event):
        return event.id == constants.EVENT_APPLICATION_STATUS and \
               event.context.get("old_status") in [constants.APPLICATION_STATUS_COMPLETED, constants.APPLICATION_STATUS_READY] and \
               event.context.get("new_status") == constants.APPLICATION_STATUS_IN_PROGRESS

    @classmethod
    def consume(cls, event):
        context = event.context
        app_id = context.get("application")
        if app_id is None:
            return
        application = models.Application.pull(app_id)
        if not application.editor:
            return

        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = application.editor
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
        notification.message = svc.message(cls.ID).format(application_title=application.bibjson().title)

        string_id_query = edges.make_url_query(query_string=application.id)
        notification.action = url_for("editor.associate_suggestions", source=string_id_query)

        svc.notify(notification)
