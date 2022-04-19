from flask import url_for

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
                event.context.get("old_status") != constants.APPLICATION_STATUS_READY and \
                event.context.get("new_status") == constants.APPLICATION_STATUS_READY

    @classmethod
    def consume(cls, event):
        context = event.context
        app_id = context.get("application")
        if app_id is None:
            return
        application = models.Application.pull(app_id)
        if application is None:
            raise exceptions.NoSuchObjectException("Unable to locate application with id {x}".format(x=app_id))

        if not application.editor_group:
            return

        # editor = "unknown editor"
        # if application.editor:
        #     editor = application.editor
        acc = models.Account.pull(event.who)

        eg = models.EditorGroup.pull_by_key("name", application.editor_group)
        managing_editor = eg.maned
        if not managing_editor:
            return

        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = managing_editor
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
        notification.message = svc.message(cls.ID).format(
            application_title=application.bibjson().title,
            editor=editor
        )

        string_id_query = edges.make_url_query(query_string=application.id)
        if application.application_type == constants.APPLICATION_TYPE_NEW_APPLICATION:
            url_for_application = url_for("admin.suggestions", source=string_id_query)
        else:
            url_for_application = url_for("admin.update_requests", source=string_id_query)
        notification.action = url_for_application

        svc.notify(notification)
