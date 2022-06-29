# ~~Notifications:Service~~
from portality import models
from portality.core import app
from portality import app_email
from portality.ui.messages import Messages
from portality.bll.exceptions import NoSuchObjectException, NoSuchPropertyException


class NotificationsService(object):
    def notify(self, notification):
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
        return app.jinja_env.globals["data"]["notifications"].get(message_id, {}).get("long")

    def short_notification(self, message_id):
        return app.jinja_env.globals["data"]["notifications"].get(message_id, {}).get("short", Messages.NOTIFY__DEFAULT_SHORT_NOTIFICATION)