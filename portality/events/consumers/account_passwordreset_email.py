from portality.util import url_for
from portality.events.consumer import EventConsumer
from portality import constants
from portality import app_email
from portality import models
from portality.core import app
from portality.bll.exceptions import NoSuchPropertyException


class AccountPasswordResetEmail(EventConsumer):
    ID = "account:password_reset:email"

    @classmethod
    def consumes(cls, event):
        return event.id == constants.EVENT_ACCOUNT_PASSWORD_RESET and event.context.get("account") is not None

    @classmethod
    def consume(cls, event):
        acc = models.Account(**event.context.get("account"))
        if not acc.reset_token or not acc.email:
            raise NoSuchPropertyException("Account {x} does not have a reset_token and/or an email address".format(x=acc.id))
        cls._send_password_reset_email(acc)

    @classmethod
    def _send_password_reset_email(cls, account: models.Account):
        reset_url = app.config.get('BASE_URL', "https://doaj.org") + url_for('account.reset', reset_token=account.reset_token)

        to = [account.email]
        fro = app.config.get('SYSTEM_EMAIL_FROM', app.config['ADMIN_EMAIL'])
        subject = app.config.get("SERVICE_NAME", "") + " - password reset"

        app_email.send_mail(to=to,
                            fro=fro,
                            subject=subject,
                            template_name="email/account_password_reset.jinja2",
                            email=account.email,
                            reset_url=reset_url,
                            forgot_pw_url=app.config.get('BASE_URL', "https://doaj.org") + url_for('account.forgot')
                            )