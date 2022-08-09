from portality.util import url_for

from portality.core import app
from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.bll import DOAJ, exceptions
from portality.lib.seamless import SeamlessException
from portality.lib.dates import human_date

class ApplicationPublisherInprogressNotify(EventConsumer):
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

        title = application.bibjson().title
        date_applied = human_date(application.date_applied)
        volunteers = app.config.get("BASE_URL") + url_for("doaj.volunteers")

        notification.long = svc.long_notification(cls.ID).format(
            title=title,
            date_applied=date_applied,
            volunteers=volunteers
        )
        notification.short = svc.short_notification(cls.ID)

        svc.notify(notification)
