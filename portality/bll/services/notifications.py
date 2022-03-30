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
        to = [acc.email]

        fro = app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org')
        subject = app.config.get("SERVICE_NAME", "") + " - " + \
                  Messages.NOTIFY__CONSUMER_EMAIL_SUBJECTS.get(
                      notification.created_by,
                      Messages.NOTIFY__DEFAULT_EMAIL_SUBJECT
                  )

        app_email.send_mail(to=to,
                            fro=fro,
                            subject=subject,
                            template_name="email/notification_email.jinja2",
                            user=acc,
                            message=notification.message,
                            action=notification.action)
