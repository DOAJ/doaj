# ~~ FlagAssigned:Consumer ~~
from portality.ui.messages import Messages
from portality.util import url_for
from portality.events.consumer import EventConsumer
from portality import constants
from portality.bll import exceptions
from portality import models
from portality.bll import DOAJ

class FlagAssigned(EventConsumer):
    ID = "flag:assigned"

    @classmethod
    def should_consume(cls, event):
        return event.id == constants.EVENT_FLAG_ASSIGNED and event.context.get("assignee") is not None

    @classmethod
    def consume(cls, event):
        assignee_id = event.context.get("assignee")
        j_source = event.context.get("journal")

        try:
            journal = models.Journal(**j_source)
        except Exception as e:
            raise exceptions.NoSuchObjectException(
                Messages.EXCEPTION_UNABLE_TO_CONSTRUCT_JOURNAL.format(x=e))

        acc = models.Account.pull(assignee_id)

        if not acc:
            raise exceptions.NoSuchObjectException(Messages.EXCEPTION_NOTIFICATION_NO_ACCOUNT.format(id=assignee_id))

        if not acc.email:
            raise exceptions.NoSuchPropertyException(Messages.EXCEPTION_NOTIFICATION_NO_EMAIL.format(x=acc.id))

        # ~~-> Notifications:Service ~~
        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_ASSIGN
        notification.who = acc.id
        notification.created_by = cls.ID
        notification.long = svc.long_notification(cls.ID).format(
            journal_title=journal.bibjson().title,
            id=journal.id)

        notification.short = svc.short_notification(cls.ID)
        notification.action = url_for("admin.journal_page", journal_id=journal.id)

        svc.notify(notification)
        return notification
