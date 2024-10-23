# ~~JournalDiscontinuingSoonNotify:Consumer~~
import json
import urllib.parse

from portality.util import url_for
from portality.events.consumer import EventConsumer
from portality.core import app
from portality import constants
from portality import models
from portality.bll import DOAJ, exceptions
from portality.lib import edges
from portality import dao

class JournalDiscontinuingSoonNotify(EventConsumer):
    ID = "journal:maned:discontinuing_soon:notify"

    @classmethod
    def should_consume(cls, event):
        return event.id == constants.EVENT_JOURNAL_DISCONTINUING_SOON and \
                event.context.get("journal") is not None and \
                event.context.get("discontinue_date") is not None

    @classmethod
    def consume(cls, event):
        journal_id = event.context.get("journal")
        discontinued_date = event.context.get("discontinue_date")

        journal = models.Journal.pull(journal_id)
        if journal is None:
            return

        if not journal.editor_group:
            return

        eg = models.EditorGroup.pull(journal.editor_group)
        managing_editor = eg.maned
        if not managing_editor:
            return

        # ~~-> Notifications:Service ~~
        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = managing_editor
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_STATUS
        notification.long = svc.long_notification(cls.ID).format(
            days=app.config.get('DISCONTINUED_DATE_DELTA',0),
            title=journal.bibjson().title,
            id=journal.id
        )
        notification.short = svc.short_notification(cls.ID)
        notification.action = url_for("admin.journal_page", journal_id=journal.id)

        svc.notify(notification)
