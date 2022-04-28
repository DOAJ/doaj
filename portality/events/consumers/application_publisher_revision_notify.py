from flask import url_for
from datetime import datetime

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
               event.context.get("application") is not None and \
               event.context.get("old_status") != constants.APPLICATION_STATUS_REVISIONS_REQUIRED and \
               event.context.get("new_status") == constants.APPLICATION_STATUS_REVISIONS_REQUIRED

    @classmethod
    def consume(cls, event):
        app_source = event.context.get("application")
        try:
            application = models.Application(**app_source)
        except SeamlessException as e:
            raise exceptions.NoSuchObjectException("Unable to construct Application from supplied source - data structure validation error, {x}".format(x=e))

        if application.owner is None:
            return

        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = application.owner
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
        datetime_object = datetime.strptime(application.date_applied, '%Y-%m-%dT%H:%M:%SZ')
        date_applied = datetime_object.strftime("%d/%b/%Y")
        notification.message = svc.message(cls.ID).format(
            application_title=application.bibjson().title,
            date_applied=date_applied
        )

        svc.notify(notification)
