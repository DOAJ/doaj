# ~~ApplicationPublisherQuickRejectNotify:Consumer~~
from portality.events import consumer_utils
from portality.lib import dates
from portality.lib.dates import FMT_DATE_HUMAN_A
from portality.util import url_for

from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.bll import DOAJ, exceptions
from portality.core import app


class ApplicationPublisherQuickRejectNotify(EventConsumer):
    ID = "application:publisher:quickreject:notify"

    @classmethod
    def should_consume(cls, event):
        return event.id == constants.EVENT_APPLICATION_STATUS and \
                event.context.get("application") is not None and \
                event.context.get("old_status") != constants.APPLICATION_STATUS_REJECTED and \
                event.context.get("new_status") == constants.APPLICATION_STATUS_REJECTED and \
                event.context.get("process") == constants.PROCESS__QUICK_REJECT

    @classmethod
    def consume(cls, event):
        app_source = event.context.get("application")
        note = event.context.get("note")
        if note:
            note = "\n\n**Reason for rejection**\n\n" + note + "\n\n"

        application = consumer_utils.parse_application(app_source)
        if not application.owner:
            return None

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
            note=note if note is not None else "",
            doaj_guide_url=app.config.get('BASE_URL', "https://doaj.org") + url_for("doaj.guide")
        )
        notification.short = svc.short_notification(cls.ID).format(
            issns=application.bibjson().issns_as_text()
        )

        # there is no action url for this notification

        svc.notify(notification)
        return notification
