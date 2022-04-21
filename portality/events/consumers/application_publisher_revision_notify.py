from flask import url_for

from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.lib import edges
from portality.bll import DOAJ, exceptions
from portality.lib.seamless import SeamlessException


class ApplicationPublisherRevisionNotify(EventConsumer):
    ID = "application:publisher:revision:notify"

    @classmethod
    def consumes(cls, event):
        return event.id == constants.EVENT_APPLICATION_STATUS and \
                event.context.get("old_status") != constants.APPLICATION_STATUS_REVISIONS_REQUIRED and \
                event.context.get("new_status") == constants.APPLICATION_STATUS_REVISIONS_REQUIRED

    @classmethod
    def consume(cls, event):
        context = event.context
        app_id = context.get("application")
        if app_id is None:
            return
        try:
            application = models.Application.pull(app_id)
        except SeamlessException:
            raise exceptions.NoSuchObjectException("Unable to locate application with id {x}".format(x=app_id))

        if application is None:
            raise exceptions.NoSuchObjectException("Unable to locate application with id {x}".format(x=app_id))

        owner = application.owner
        if owner is None:
            raise exceptions.NoSuchPropertyException("No owner found for application with id {x}".format(x=app_id))

        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = owner
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
        from datetime import datetime
        datetime_object = datetime.strptime(application.date_applied, '%Y-%m-%dT%H:%M:%SZ')
        date_applied = datetime_object.strftime("%d/%b/%Y")
        notification.message = svc.message(cls.ID).format(
            application_title=application.bibjson().title,
            date_applied=date_applied
        )

        svc.notify(notification)
