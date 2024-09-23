# ~~ApplicationManedReadyNotify:Consumer~~
from portality.events import consumer_utils
from portality.util import url_for
from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.bll import DOAJ, exceptions


class ApplicationManedReadyNotify(EventConsumer):
    ID = "application:maned:ready:notify"

    @classmethod
    def should_consume(cls, event):
        return event.id == constants.EVENT_APPLICATION_STATUS and \
                event.context.get("application") is not None and \
                event.context.get("old_status") != constants.APPLICATION_STATUS_READY and \
                event.context.get("new_status") == constants.APPLICATION_STATUS_READY

    @classmethod
    def consume(cls, event):
        app_source = event.context.get("application")

        application = consumer_utils.parse_application(app_source)
        if not application.editor_group:
            return


        eg = models.EditorGroup.pull_by_key("name", application.editor_group)
        managing_editor = eg.maned
        if not managing_editor:
            return

        editor = eg.editor
        if not editor:
            editor = "unknown editor"

        # ~~-> Notifications:Service ~~
        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = managing_editor
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
        notification.long = svc.long_notification(cls.ID).format(
            application_title=application.bibjson().title,
            editor=editor
        )
        notification.short = svc.short_notification(cls.ID).format(
            issns=application.bibjson().issns_as_text()
        )
        notification.action = url_for("admin.application", application_id=application.id)

        svc.notify(notification)
