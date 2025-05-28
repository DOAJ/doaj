# ~~AdminAlerts:Service~~
from portality import app_email
from portality import models
from portality.core import app
from portality.ui import templates


class AdminAlertsService(object):
    def alert(self, source, message):
        a = models.AdminAlert()
        a.source = source
        a.message = message
        a.state = models.AdminAlert.STATE_NEW
        a.save()

        # now send an email to the sysadmin email
        email = app.config.get("ERROR_LOGGING_EMAIL", None)
        if email is None:
            return a

        to = [email]
        fro = app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org')
        subject = app.config.get("SERVICE_NAME", "") + " - admin alert from " + source

        # ~~-> Email:Library ~~
        app_email.send_mail(to=to,
                            fro=fro,
                            subject=subject,
                            template_name=templates.EMAIL_NOTIFICATION,
                            user=None,  # no user for admin alerts
                            message=message)

        return a

    def set_in_progress(self, alert_id: str):
        # ~~-> Notifications:Query ~~
        a = models.AdminAlert.pull(alert_id)
        if not a:
            return
        a.state = models.AdminAlert.STATE_IN_PROGRESS
        a.save()
        return a

    def set_closed(self, alert_id: str):
        # ~~-> Notifications:Query ~~
        a = models.AdminAlert.pull(alert_id)
        if not a:
            return
        a.state = models.AdminAlert.STATE_CLOSED
        a.save()
        return a
