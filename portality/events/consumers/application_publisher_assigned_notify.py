# ~~ApplicationPublisherAssignedNotify:Consumer~~
from portality.events import consumer_utils
from portality.util import url_for
from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.lib import dates
from portality.core import app


class ApplicationPublisherAssignedNotify(EventConsumer):
    ID = "application:publisher:assigned:notify"

    @classmethod
    def should_consume(cls, event):
        if event.id != constants.EVENT_APPLICATION_ASSED_ASSIGNED:
            return False

        if not consumer_utils.is_enable_publisher_email():
            return False

        app_source = event.context.get("application")
        if app_source is None:
            return False

        if event.context.get("old_editor") not in [None, ""]:
            return False

        if event.context.get("new_editor") in [None, ""]:
            return False

        application = consumer_utils.parse_application(app_source)
        is_new_application = application.application_type == constants.APPLICATION_TYPE_NEW_APPLICATION
        return is_new_application

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
            application_date=dates.human_date(application.date_applied),
            volunteers_url=app.config.get('BASE_URL', "https://doaj.org") + url_for("doaj.volunteers"),
        )
        notification.short = svc.short_notification(cls.ID).format(
            issns=consumer_utils.parse_email_issns(application.bibjson().issns())
        )
        # note that there is no action url

        svc.notify(notification)
