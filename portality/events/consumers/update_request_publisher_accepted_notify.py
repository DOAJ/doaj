# ~~UpdateRequestPublisherAcceptedNotify:Consumer~~
from portality.util import url_for

from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.lib import edges, dates
from portality.bll import DOAJ, exceptions
from portality.core import app


class UpdateRequestPublisherAcceptedNotify(EventConsumer):
    ID = "update_request:publisher:accepted:notify"

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

        if event.context.get("new_status") != constants.APPLICATION_STATUS_ACCEPTED:
            return False

        try:
            application = models.Application(**app_source)
        except Exception as e:
            raise exceptions.NoSuchObjectException("Unable to construct Application from supplied source - data structure validation error, {x}".format(x=e))

        is_update_request = application.application_type == constants.APPLICATION_TYPE_UPDATE_REQUEST
        return is_update_request

    @classmethod
    def consume(cls, event):
        # TODO: in the long run this needs to move out to the user's email preferences but for now it
        # is here to replicate the behaviour in the code it replaces
        if not app.config.get("ENABLE_PUBLISHER_EMAIL", False):
            return

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

        notification.long = svc.long_notification(cls.ID).format(
            application_title=application.bibjson().title,
            application_date=dates.human_date(application.date_applied),
            publisher_dashboard_url=app.config.get('BASE_URL', "https://doaj.org") + url_for("publisher.journals")
        )
        notification.short = svc.short_notification(cls.ID).format(
            issns=", ".join(issn for issn in application.bibjson().issns())
        )

        notification.action = url_for("publisher.journals")

        svc.notify(notification)
