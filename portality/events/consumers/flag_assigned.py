# ~~ FlagAssigned:Consumer ~~
from portality.ui.messages import Messages
from portality.util import url_for
from portality.events.consumer import EventConsumer
from portality import constants
from portality import app_email
from portality import models
from portality.core import app
from portality.bll.exceptions import NoSuchPropertyException
from portality.ui import templates


class FlagAssigned(EventConsumer):
    ID = "flag:assigned"

    @classmethod
    def should_consume(cls, event):
        return event.id == constants.EVENT_FLAG_ASSIGNED and event.context.get("assignee") is not None

    @classmethod
    def consume(cls, event):
        context = event.context
        acc = models.Account(**context.get("assignee"))
        j_source = event.context.get("journal")

        try:
            journal = models.Journal(**j_source)
        except Exception as e:
            raise exceptions.NoSuchObjectException(
                Messages.EXCEPTION_UNABLE_TO_CONSTRUCT_JOURNAL.format(x=e))

        if not acc.email:
            raise NoSuchPropertyException(Messages.EXCEPTION_NOTIFICATION_NO_EMAIL.format(x=acc.id))
        cls._send_flag_assigned_email(acc, journal)

    @classmethod
    def _send_flag_assigned_email(cls, assignee: models.Account, journal: models.Journal):
        # ~~->FlagAssigned:Email~~

        to = [assignee.email]
        fro = app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org')
        subject = app.config.get("SERVICE_NAME", "") + " - a new flagged assigned"

        journal_url = url_root + url_for("admin/journal", source=journal.id)

        app_email.send_mail(to=to,
                            fro=fro,
                            subject=subject,
                            template_name=templates.FLAG_ASSIGNED,
                            assignee=assignee.name if name in assignee else assignee.id,
                            journal_title=journal.title,
                            journal_url=journal_url)