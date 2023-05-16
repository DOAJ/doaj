# ~~UpdateRequestPublisherRejectedNotify:Consumer~~

from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.bll import DOAJ, exceptions
from portality.core import app
from portality.lib import dates
from portality.lib.dates import FMT_DATE_HUMAN_A


class UpdateRequestPublisherRejectedNotify(EventConsumer):
    ID = "update_request:publisher:rejected:notify"

    @classmethod
    def consumes(cls, event):
        if event.id != constants.EVENT_APPLICATION_STATUS:
            return False

        # TODO: in the long run this needs to move out to the user's email preferences but for now it
        # is here to replicate the behaviour in the code it replaces
        if not app.config.get("ENABLE_PUBLISHER_EMAIL", False):
            return False

        app_source = event.context.get("application")
        if app_source is None:
            return False

        if event.context.get("new_status") != constants.APPLICATION_STATUS_REJECTED:
            return False

        if event.context.get("old_status") == constants.APPLICATION_STATUS_REJECTED:
            return False

        try:
            application = models.Application(**app_source)
        except Exception as e:
            raise exceptions.NoSuchObjectException("Unable to construct Application from supplied source - data structure validation error, {x}".format(x=e))

        is_update_request = application.application_type == constants.APPLICATION_TYPE_UPDATE_REQUEST
        return is_update_request

    @classmethod
    def consume(cls, event):
        app_source = event.context.get("application")

        try:
            application = models.Application(**app_source)
        except Exception as e:
            raise exceptions.NoSuchObjectException("Unable to construct Application from supplied source - data structure validation error, {x}".format(x=e))

        if not application.owner:
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
            title=application.bibjson().title,
            date_applied=date_applied,
        )
        notification.short = svc.short_notification(cls.ID)

        # there is no action url associated with this notification

        svc.notify(notification)
