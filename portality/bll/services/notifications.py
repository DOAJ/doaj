# ~~Notifications:Service~~
from portality import models
from portality.core import app
from portality import app_email
from portality.ui.messages import Messages
from portality.bll.exceptions import NoSuchObjectException, NoSuchPropertyException


class NotificationsService(object):
    def notify(self, notification: models.Notification):
        # first just save the notification
        notification.save()

        # now send an email to the notification target
        acc = models.Account.pull(notification.who)
        if acc is None:
            raise NoSuchObjectException(Messages.EXCEPTION_NOTIFICATION_NO_ACCOUNT.format(x=notification.who))

        if acc.email is None:
            raise NoSuchPropertyException(Messages.EXCEPTION_NOTIFICATION_NO_EMAIL.format(x=notification.who))

        to = [acc.email]
        fro = app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org')
        subject = app.config.get("SERVICE_NAME", "") + " - " + notification.short

        # ~~-> Email:Library ~~
        app_email.send_markdown_mail(to=to,
                            fro=fro,
                            subject=subject,
                            template_name="email/notification_email.jinja2",
                            markdown_template_name="email/notification_email.jinja2",    # for the moment the markdown and plaintext templates are the same
                            user=acc,
                            message=notification.long,
                            action=notification.action,
                            url_root=app.config.get("BASE_URL"))

        return notification

    def long_notification(self, message_id):
        # ~~-> Notifications:Data ~~
        return app.jinja_env.globals["data"]["notifications"].get(message_id, {}).get("long")

    def short_notification(self, message_id):
        # ~~-> Notifications:Data ~~
        return app.jinja_env.globals["data"]["notifications"].get(message_id, {}).get("short", Messages.NOTIFY__DEFAULT_SHORT_NOTIFICATION)

    def top_notifications(self, account: models.Account, size: int = 10):
        # ~~-> TopNotifications:Query ~~
        q = TopNotificationsQuery(account.id, size)
        top = models.Notification.object_query(q.query())
        return top

    def notification_seen(self, account: models.Account, notification_id: str):
        note = models.Notification.pull(notification_id)
        if not note:
            raise NoSuchObjectException(Messages.EXCEPTION_NOTIFICATION_NO_NOTIFICATION.format(n=notification_id))
        if account.id == note.who or account.is_super:
            if not note.is_seen():
                note.set_seen()
                note.save()
            return True
        return False


class TopNotificationsQuery(object):
    # ~~->$ TopNotifications:Query ~~
    # ~~^-> Elasticsearch:Technology ~~
    def __init__(self, account_id, size=10):
        self.account_id = account_id
        self.size = size

    def query(self):
        return {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"who.exact": self.account_id}}
                    ]
                }
            },
            "sort": [{"created_date": {"order": "desc"}}],
            "size": self.size
        }