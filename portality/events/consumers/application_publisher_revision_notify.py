# ~~ApplicationPublisherRevisionNotify:Consumer~~

from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.bll import DOAJ, exceptions
from portality.lib import dates
from portality.lib.dates import FMT_DATE_HUMAN_A
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

        # ~~-> Notifications:Service ~~
        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = application.owner
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
        datetime_object = dates.parse(application.date_applied)
        date_applied = datetime_object.strftime(FMT_DATE_HUMAN_A)
        notification.long = svc.long_notification(cls.ID).format(
            application_title=application.bibjson().title,
            date_applied=date_applied
        )
        notification.short = svc.short_notification(cls.ID)

        svc.notify(notification)
