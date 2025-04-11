# ~~UpdateRequestPublisherAssignedNotify:Consumer~~
from portality.events import consumer_utils
from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.lib import dates
from portality.core import app
from portality.models import Account


class UpdateRequestPublisherAssignedNotify(EventConsumer):
    ID = "update_request:publisher:assigned:notify"

    @classmethod
    def should_consume(cls, event):
        if event.id != constants.EVENT_APPLICATION_ASSED_ASSIGNED:
            return False

        if not Account.is_enable_publisher_email():
            return False

        app_source = event.context.get("application")
        if app_source is None:
            return False

        if event.context.get("old_editor") not in [None, ""]:
            return False

        if event.context.get("new_editor") in [None, ""]:
            return False

        application = consumer_utils.parse_application(app_source)
        is_update_request = application.application_type == constants.APPLICATION_TYPE_UPDATE_REQUEST
        return is_update_request

    @classmethod
    def consume(cls, event):
        app_source = event.context.get("application")

        application = consumer_utils.parse_application(app_source)
        if not application.owner:
            raise exceptions.NoSuchPropertyException("Application {x} does not have property `owner`".format(x=application.id))

        # ~~-> Notifications:Service ~~
        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = application.owner
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_ASSIGN
        notification.long = svc.long_notification(cls.ID).format(
            application_title=application.bibjson().title,
            application_date=dates.human_date(application.date_applied)
        )
        notification.short = svc.short_notification(cls.ID).format(
            issns=application.bibjson().issns_as_text()
        )
        # note that there is no action url

        svc.notify(notification)
        return notification
