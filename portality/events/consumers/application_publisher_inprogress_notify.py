from flask import url_for
from datetime import datetime

from portality.core import app
from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.lib import edges
from portality.bll import DOAJ, exceptions
from portality.lib.seamless import SeamlessException
from portality.lib.dates import human_date

class ApplicationPublisherInprogresNotify(EventConsumer):
    ID = "application:publisher:inprogress:notify"

    @classmethod
    def consumes(cls, event):
        return event.id == constants.EVENT_APPLICATION_STATUS and \
               event.context.get("application") is not None and \
               event.context.get("old_status") == constants.APPLICATION_STATUS_PENDING and \
               event.context.get("new_status") == constants.APPLICATION_STATUS_IN_PROGRESS

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
        notification.message = svc.message(cls.ID).format(
            application_title=application.bibjson().title,
            date_applied=human_date(application.date_applied),
            volunteers=app.config.get("BASE_URL") + url_for("doaj.volunteers")
        )

        svc.notify(notification)