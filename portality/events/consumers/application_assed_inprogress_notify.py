from flask import url_for

from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.lib import edges
from portality.ui.messages import Messages
from portality.bll import DOAJ
from portality.core import app


class ApplicationAssedInprogressNotify(EventConsumer):
    ID = "application:assed:inprogress:notify"

    @classmethod
    def consumes(cls, event):
        return event.id == constants.EVENT_APPLICATION_STATUS and \
               event.context.get("old_status") == constants.APPLICATION_STATUS_COMPLETED and \
               event.context.get("new_status") == constants.APPLICATION_STATUS_IN_PROGRESS

    @classmethod
    def consume(cls, event):
        context = event.context
        app_id = context.get("application")
        application = models.Application.pull(app_id)
        if not application.editor:
            return

        notification = models.Notification()
        notification.who = application.editor
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
        notification.message = Messages.NOTIFY__APPLICATION_ASSED_INPROGESS.format(application_title=application.bibjson().title)

        url_root = app.config.get("BASE_URL")
        string_id_query = edges.make_url_query(query_string=application.id)
        url_for_application = url_root + url_for("editor.associate_suggestions", source=string_id_query)
        notification.action = url_for_application

        svc = DOAJ.notificationsService()
        svc.notify(notification)
