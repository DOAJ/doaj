# ~~Notifications:Service~~
from portality import models
from portality.core import app
from portality import app_email
from portality.ui.messages import Messages


class NotificationsService(object):
    def notify(self, notification):
        # first just save the notification
        notification.save()

        # now send an email to the notification target
        acc = models.Account.pull(notification.who)
        if acc is None:
            return

        if acc.email is None:
            return

        to = [acc.email]
        fro = app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org')
        subject = app.config.get("SERVICE_NAME", "") + " - " + self.email_subject(notification.created_by)

        app_email.send_mail(to=to,
                            fro=fro,
                            subject=subject,
                            template_name="email/notification_email.jinja2",
                            user=acc,
                            message=notification.message,
                            action=notification.action,
                            url_root=app.config.get("BASE_URL"))

    def message(self, message_id):
        return app.jinja_env.globals["data"]["notifications"].get(message_id, {}).get("message")

    def email_subject(self, message_id):
        return app.jinja_env.globals["data"]["notifications"].get(message_id, {}).get("email_subject", Messages.NOTIFY__DEFAULT_EMAIL_SUBJECT)