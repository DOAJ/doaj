# ~~JournalDiscontinuingSoonNotify:Consumer~~
import json
from portality.util import url_for

from portality.events.consumer import EventConsumer
from portality.core import app
from portality import constants
from portality import models
from portality.bll import DOAJ
from portality.bll import exceptions


class JournalDiscontinuingSoonNotify(EventConsumer):
    ID = "journal:assed:discontinuing_soon:notify"

    @classmethod
    def consumes(cls, event):
        return event.id == constants.EVENT_JOURNAL_DISCONTINUING_SOON and \
               event.context.get("job") is not None and \
                event.context.get("data") is not None

    @classmethod
    def consume(cls, event):

        source = event.context.get("job")
        try:
            job = models.BackgroundJob(**source)
        except Exception as e:
            raise exceptions.NoSuchObjectException(
                "Unable to construct a BackgroundJob object from the data supplied {x}".format(x=e))

        if job.user is None:
            return

        acc = models.Account.pull(job.user)
        if acc is None or not acc.has_role("admin"):
            return


        journals = []
        for j in data:
            journals.append(j["id"])

        # ~~-> Notifications:Service ~~
        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = acc.id
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_ASSIGN
        notification.long = svc.long_notification(cls.ID).format(
            days=app.config.get('DISCONTINUED_DATE_DELTA',1),
            data=json.dumps({"data": data}, indent=4, separators=(',', ': '))
        )
        notification.short = svc.short_notification(cls.ID)
        notification.action = url_for("dashboard.notifications")

        svc.notify(notification)
