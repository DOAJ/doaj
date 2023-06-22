# ~~ApplicationEditorInProgressNotify:Consumer~~
from portality.util import url_for

from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.bll import DOAJ, exceptions
from portality.lib.seamless import SeamlessException


class ApplicationEditorInProgressNotify(EventConsumer):
    ID = "application:editor:inprogress:notify"

    @classmethod
    def consumes(cls, event):
        return event.id == constants.EVENT_APPLICATION_STATUS and \
                event.context.get("old_status") in [constants.APPLICATION_STATUS_READY, constants.APPLICATION_STATUS_COMPLETED] and \
                event.context.get("new_status") == constants.APPLICATION_STATUS_IN_PROGRESS

    @classmethod
    def consume(cls, event):
        context = event.context
        app = context.get("application")
        if app is None:
            return
        try:
            application = models.Application(**app)
        except SeamlessException:
            raise exceptions.NoSuchObjectException("Unable to create application model from source")

        if application is None:
            raise exceptions.NoSuchObjectException("Unable to create application model from source")

        if not application.editor_group:
            return

        # Notification is to the editor in charge of this application's assigned editor group
        editor_group_name = application.editor_group
        editor_group_id = models.EditorGroup.group_exists_by_name(name=editor_group_name)
        eg = models.EditorGroup.pull(editor_group_id)
        group_editor = eg.editor

        if not group_editor:
            return

        # ~~-> Notifications:Service ~~
        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = group_editor
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
        notification.long = svc.long_notification(cls.ID).format(
            application_title=application.bibjson().title
        )
        notification.short = svc.short_notification(cls.ID).format(
            issns=", ".join(issn for issn in application.bibjson().issns())
        )
        notification.action = url_for("editor.application", application_id=application.id)

        svc.notify(notification)
