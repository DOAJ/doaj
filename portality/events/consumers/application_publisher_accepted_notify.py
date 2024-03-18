# ~~ApplicationPublisherAcceptedNotify:Consumer~~
from portality import constants
from portality import models
from portality.bll import DOAJ
from portality.core import app
from portality.events import consumer_utils
from portality.events.consumer import EventConsumer
from portality.lib import dates
from portality.models import Account
from portality.util import url_for


class ApplicationPublisherAcceptedNotify(EventConsumer):
    ID = "application:publisher:accepted:notify"

    @classmethod
    def should_consume(cls, event):
        if event.id != constants.EVENT_APPLICATION_STATUS:
            return False

        if not Account.is_enable_publisher_email():
            return False

        app_source = event.context.get("application")
        if app_source is None:
            return False

        if event.context.get("new_status") != constants.APPLICATION_STATUS_ACCEPTED:
            return False

        application = consumer_utils.parse_application(app_source)
        is_new_application = application.application_type == constants.APPLICATION_TYPE_NEW_APPLICATION
        return is_new_application

    @classmethod
    def consume(cls, event):
        if not Account.is_enable_publisher_email():
            return

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

        notification.long = svc.long_notification(cls.ID).format(
            application_title=application.bibjson().title,
            application_date=dates.human_date(application.date_applied),
            publisher_dashboard_url=app.config.get("BASE_URL") + url_for("publisher.journals"),
            faq_url=app.config.get("BASE_URL") + url_for("doaj.faq")
        )
        notification.short = svc.short_notification(cls.ID).format(
            issns=application.bibjson().issns_as_text()
        )

        notification.action = url_for("publisher.journals")

        svc.notify(notification)
