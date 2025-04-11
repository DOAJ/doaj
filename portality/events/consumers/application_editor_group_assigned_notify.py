# ~~ ApplicatioditorGroupAssignedNotify:Consumer~~
from portality.events import consumer_utils
from portality.util import url_for
from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.bll import DOAJ
from portality.bll import exceptions


class ApplicationEditorGroupAssignedNotify(EventConsumer):
    ID = "application:editor_group:assigned:notify"

    @classmethod
    def should_consume(cls, event):
        return event.id == constants.EVENT_APPLICATION_EDITOR_GROUP_ASSIGNED and \
               event.context.get("application") is not None

    @classmethod
    def consume(cls, event):
        app_source = event.context.get("application")

        application = consumer_utils.parse_application(app_source)

        if application.application_type != constants.APPLICATION_TYPE_NEW_APPLICATION:
            return None

        if not application.editor_group:
            return None

        editor_group = models.EditorGroup.pull_by_key("name", application.editor_group)

        if not editor_group.editor:
            raise exceptions.NoSuchPropertyException("Editor Group {x} does not have property `editor`".format(x=editor_group.id))

        # ~~-> Notifications:Service ~~
        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = editor_group.editor
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_ASSIGN

        notification.long = svc.long_notification(cls.ID).format(
            journal_name=application.bibjson().title
        )
        notification.short = svc.short_notification(cls.ID).format(
            issns=application.bibjson().issns_as_text()
        )

        notification.action = url_for("editor.application", application_id=application.id)

        svc.notify(notification)
        return notification
