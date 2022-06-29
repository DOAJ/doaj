from flask import url_for
from datetime import datetime

from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.lib import edges
from portality.bll import DOAJ, exceptions


class ApplicationPublisherQuickRejectNotify(EventConsumer):
    ID = "application:publisher:quickreject:notify"

    @classmethod
    def consumes(cls, event):
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

        try:
            application = models.Application(**app_source)
        except Exception as e:
            raise exceptions.NoSuchObjectException("Unable to construct Application from supplied source - data structure validation error, {x}".format(x=e))

        if not application.owner:
            return

        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = application.owner
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
        datetime_object = datetime.strptime(application.date_applied, '%Y-%m-%dT%H:%M:%SZ')
        date_applied = datetime_object.strftime("%d/%b/%Y")
        notification.long = svc.long_notification(cls.ID).format(
            title=application.bibjson().title,
            date_applied=date_applied,
            note=note,
            doaj_guide_url=url_for("doaj.guide", _external=True)
        )
        notification.short = svc.short_notification(cls.ID)

        # there is no action url for this notification

        svc.notify(notification)
