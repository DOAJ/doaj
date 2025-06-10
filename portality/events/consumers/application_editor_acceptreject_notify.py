# ~~ApplicationAssedInProgressNotify:Consumer~~
from portality.events import consumer_utils
from portality.util import url_for
from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.bll import DOAJ


class ApplicationEditorAcceptRejectNotify(EventConsumer):
    ID = "application:editor:acceptreject:notify"

    @classmethod
    def should_consume(cls, event):
        return event.id == constants.EVENT_APPLICATION_STATUS and \
               event.context.get("application") is not None and \
               event.context.get("new_status") in [constants.APPLICATION_STATUS_ACCEPTED, constants.APPLICATION_STATUS_REJECTED]

    @classmethod
    def consume(cls, event):
        app_source = event.context.get("application")

        application = consumer_utils.parse_application(app_source)

        if application.application_type != constants.APPLICATION_TYPE_NEW_APPLICATION:
            return None

        if not application.editor_group:
            return None

        eg = models.EditorGroup.pull_by_key("name", application.editor_group)
        if not eg:
            return None

        if not eg.editor:
            return None

        acc = models.Account.pull(eg.editor)
        if acc.has_role(constants.ROLE_ADMIN):
            return None

        # ~~-> Notifications:Service ~~
        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = eg.editor
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
        notification.long = svc.long_notification(cls.ID).format(
            application_title=application.bibjson().title,
            decision=application.application_status
        )

        notification.short = svc.short_notification(cls.ID).format(
            issns=application.bibjson().issns_as_text(),
            decision=application.application_status
        )
        notification.action = url_for("editor.application", application_id=application.id)

        svc.notify(notification)
        return notification
