# ~~UpdateRequestPublisherSubmittedNotify:Consumer~~
from typing import TypedDict

from portality import constants
from portality import models
from portality.bll import DOAJ
from portality.events import consumer_utils
from portality.events.consumer import EventConsumer
from portality.lib import dates
from portality.util import url_for


class UpdateRequestPublisherSubmittedNotify(EventConsumer):
    ID = "update_request:publisher:submitted:notify"

    class Context(TypedDict):
        # no usage, just for developer reference
        application: dict

    @classmethod
    def should_consume(cls, event):
        if event.id != constants.EVENT_APPLICATION_UR_SUBMITTED:
            return False

        if not consumer_utils.is_enable_publisher_email():
            return False

        app_source = event.context.get("application")
        if app_source is None:
            return False

        application = consumer_utils.parse_application(app_source)
        if application.application_type != constants.APPLICATION_TYPE_UPDATE_REQUEST:
            return False

        if not application.owner:
            return False

        return True

    @classmethod
    def consume(cls, event):
        application = consumer_utils.parse_application(event.context.get("application"))

        # ~~-> Notifications:Service ~~
        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = application.owner
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE

        notification.long = svc.long_notification(cls.ID).format(
            title=application.bibjson().title,
            date_applied=dates.human_date(application.date_applied),
        )
        notification.short = svc.short_notification(cls.ID).format(
            issns=consumer_utils.parse_email_issns(application.bibjson().issns())
        )

        notification.action = url_for("publisher.journals")

        svc.notify(notification)
