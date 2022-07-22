# from flask import url_for
from portality.util import url_for

from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.lib import edges
from portality.bll import DOAJ, exceptions


class ApplicationManedReadyNotify(EventConsumer):
    ID = "application:maned:ready:notify"

    @classmethod
    def consumes(cls, event):
        return event.id == constants.EVENT_APPLICATION_STATUS and \
                event.context.get("application") is not None and \
                event.context.get("old_status") != constants.APPLICATION_STATUS_READY and \
                event.context.get("new_status") == constants.APPLICATION_STATUS_READY

    @classmethod
    def consume(cls, event):
        app_source = event.context.get("application")

        try:
            application = models.Application(**app_source)
        except Exception as e:
            raise exceptions.NoSuchObjectException("Unable to construct Application from supplied source - data structure validation error, {x}".format(x=e))

        if not application.editor_group:
            return

        editor = "unknown editor"
        if application.editor:
            editor = application.editor

        eg = models.EditorGroup.pull_by_key("name", application.editor_group)
        managing_editor = eg.maned
        if not managing_editor:
            return

        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = managing_editor
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
        notification.long = svc.long_notification(cls.ID).format(
            application_title=application.bibjson().title,
            editor=editor
        )
        notification.short = svc.short_notification(cls.ID)

        # don't make the escaped query, as url_for is also going to escape it, and it will wind up double-escaped!
        # note we're using the doaj url_for wrapper, not the flask url_for directly, due to the request context hack required
        string_id_query = edges.make_query_json(query_string=application.id)
        if application.application_type == constants.APPLICATION_TYPE_NEW_APPLICATION:
            url_for_application = url_for("admin.suggestions", source=string_id_query)
        else:
            url_for_application = url_for("admin.update_requests", source=string_id_query)
        notification.action = url_for_application

        svc.notify(notification)
