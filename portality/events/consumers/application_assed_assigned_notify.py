# ~~ ApplicationAssedAssignedNotify:Consumer ~~
from portality.events import consumer_utils
from portality.util import url_for
from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.bll import DOAJ
from portality.bll import exceptions


class ApplicationAssedAssignedNotify(EventConsumer):
    ID = "application:assed:assigned:notify"

    @classmethod
    def should_consume(cls, event):
        return event.id == constants.EVENT_APPLICATION_ASSED_ASSIGNED and \
               event.context.get("application") is not None

    @classmethod
    def consume(cls, event):
        app_source = event.context.get("application")

        application = consumer_utils.parse_application(app_source)
        if not application.editor:
            raise exceptions.NoSuchPropertyException("Application {x} does not have property `editor`".format(x=application.id))

        # ~~-> Notifications:Service ~~
        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = application.editor
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_ASSIGN
        notification.long = svc.long_notification(cls.ID).format(
            journal_title=application.bibjson().title,
            group_name=application.editor_group
        )
        notification.short = svc.short_notification(cls.ID).format(
            issns=application.bibjson().issns_as_text()
        )
        notification.action = url_for("editor.application", application_id=application.id)

        svc.notify(notification)
        return notification
