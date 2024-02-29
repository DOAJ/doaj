# ~~UpdateRequestPublisherRejectedNotify:Consumer~~
from portality import constants
from portality import models
from portality.bll import DOAJ
from portality.events import consumer_utils
from portality.events.consumer import EventConsumer
from portality.lib import dates
from portality.lib.dates import FMT_DATE_HUMAN_A


class UpdateRequestPublisherRejectedNotify(EventConsumer):
    ID = "update_request:publisher:rejected:notify"

    @classmethod
    def should_consume(cls, event):
        if event.id != constants.EVENT_APPLICATION_STATUS:
            return False

        if not consumer_utils.is_enable_publisher_email():
            return False

        app_source = event.context.get("application")
        if app_source is None:
            return False

        if event.context.get("new_status") != constants.APPLICATION_STATUS_REJECTED:
            return False

        if event.context.get("old_status") == constants.APPLICATION_STATUS_REJECTED:
            return False

        application = consumer_utils.parse_application(app_source)
        is_update_request = application.application_type == constants.APPLICATION_TYPE_UPDATE_REQUEST
        return is_update_request

    @classmethod
    def consume(cls, event):
        app_source = event.context.get("application")

        application = consumer_utils.parse_application(app_source)
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
        notification.short = svc.short_notification(cls.ID).format(
            issns=consumer_utils.parse_email_issns(application.bibjson().issns())
        )

        # there is no action url associated with this notification

        svc.notify(notification)
