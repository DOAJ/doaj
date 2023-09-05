# ~~ApplicationPublisherAssignedNotify:Consumer~~
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
    def consumes(cls, event):
        if event.id != constants.EVENT_APPLICATION_ASSED_ASSIGNED:
            return False

        # TODO: in the long run this needs to move out to the user's email preferences but for now it
        # is here to replicate the behaviour in the code it replaces
        if not app.config.get("ENABLE_PUBLISHER_EMAIL", False):
            return False

        app_source = event.context.get("application")
        if app_source is None:
            return False

        if event.context.get("old_editor") not in [None, ""]:
            return False

        if event.context.get("new_editor") in [None, ""]:
            return False

        try:
            application = models.Application(**app_source)
        except Exception as e:
            raise exceptions.NoSuchObjectException("Unable to construct Application from supplied source - data structure validation error, {x}".format(x=e))

        is_new_application = application.application_type == constants.APPLICATION_TYPE_NEW_APPLICATION
        return is_new_application

    @classmethod
    def consume(cls, event):
        app_source = event.context.get("application")

        try:
            application = models.Application(**app_source)
        except Exception as e:
            raise exceptions.NoSuchObjectException("Unable to construct Application from supplied source - data structure validation error, {x}".format(x=e))

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
            issns=", ".join(issn for issn in application.bibjson().issns())
        )
        # note that there is no action url

        svc.notify(notification)
