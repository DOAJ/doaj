# ~~Notifications:Service~~
from portality import models
from portality.core import app
from portality import app_email
from portality.ui.messages import Messages
from portality.bll.exceptions import NoSuchObjectException, NoSuchPropertyException
from datetime import datetime
from portality.lib import dates


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

    def mark_all_as_seen(self, account: models.Account=None, until: datetime=None):
        account_id = None if account is None else account.id
        q = NotificationsQuery(account_id, until, False)
        for notification in models.Notification.scroll(q.query()):
            notification.set_seen()
            notification.save()


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


class NotificationsQuery(object):
    def __init__(self, account_id=None, until=None, seen=None):
        self._account_id = account_id
        self._until = until
        self._seen = seen

    def query(self):
        musts = []
        must_nots = []
        if self._account_id:
            musts.append({"term": {"who.exact": self._account_id}})

        if self._until:
            musts.append({"range": {"created_date": {"lte": dates.format(self._until, format="%Y-%m-%dT%H:%M:%S")}}})

        if self._seen is not None:
            if self._seen is True:
                musts.append({"exists": {"field": "seen_date"}})
            else:
                must_nots.append({"exists": {"field": "seen_date"}})

        if len(musts) > 0 or len(must_nots) > 0:
            q = {"query": {"bool": {}}}
            if len(musts) > 0:
                q["query"]["bool"]["must"] = musts
            if len(must_nots) > 0:
                q["query"]["bool"]["must_not"] = must_nots

        else:
            return {"query": {"match_all": {}}}
