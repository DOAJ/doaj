# from flask import url_for
from portality.util import url_for

from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.lib import edges
from portality.bll import DOAJ, exceptions


class ApplicationAssedInprogressNotify(EventConsumer):
    ID = "application:assed:inprogress:notify"

    @classmethod
    def consumes(cls, event):
        return event.id == constants.EVENT_APPLICATION_STATUS and \
               event.context.get("application") is not None and \
               event.context.get("old_status") in [constants.APPLICATION_STATUS_COMPLETED, constants.APPLICATION_STATUS_READY] and \
               event.context.get("new_status") == constants.APPLICATION_STATUS_IN_PROGRESS

    @classmethod
    def consume(cls, event):
        app_source = event.context.get("application")

        try:
            application = models.Application(**app_source)
        except Exception as e:
            raise exceptions.NoSuchObjectException("Unable to construct Application from supplied source - data structure validation error, {x}".format(x=e))

        if not application.editor:
            return

        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = application.editor
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
        notification.long = svc.long_notification(cls.ID).format(application_title=application.bibjson().title)
        notification.short = svc.short_notification(cls.ID)

        # don't make the escaped query, as url_for is also going to escape it, and it will wind up double-escaped!
        string_id_query = edges.make_query_json(query_string=application.id)
        # note we're using the doaj url_for wrapper, not the flask url_for directly, due to the request context hack required
        notification.action = url_for("editor.associate_suggestions", source=string_id_query)

        svc.notify(notification)
