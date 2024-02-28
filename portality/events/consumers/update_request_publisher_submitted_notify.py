# ~~UpdateRequestPublisherAcceptedNotify:Consumer~~
from typing import TypedDict

from portality import constants
from portality import models
from portality.bll import DOAJ
from portality.core import app
from portality.events.consumer import EventConsumer
from portality.lib import dates
from portality.util import url_for


class UpdateRequestPublisherSubmittedNotify(EventConsumer):
    ID = "update_request:publisher:submitted:notify"

    class Context(TypedDict):
        # no usage, just for developer reference
        title: str
        date_applied: str
        issns: list

    @classmethod
    def should_consume(cls, event):
        return event.id == constants.EVENT_APPLICATION_UR_SUBMITTED and event.who

    @classmethod
    def consume(cls, event):
        if not app.config.get("ENABLE_PUBLISHER_EMAIL", False):
            return

        # ~~-> Notifications:Service ~~
        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = event.who
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE

        notification.long = svc.long_notification(cls.ID).format(
            application_title=event.context.get('application_title', '<Missing Title>'),
            date_applied=dates.human_date(event.context.get('date_applied', dates.DEFAULT_TIMESTAMP_VAL)),
        )
        notification.short = svc.short_notification(cls.ID).format(
            issns=", ".join(issn for issn in event.context.get('issns', []))
        )

        notification.action = url_for("publisher.journals")

        svc.notify(notification)
