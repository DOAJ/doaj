# ~~ AccountCreatedEmail:Consumer ~~
from portality.util import url_for
from portality.events.consumer import EventConsumer
from portality import constants
from portality import app_email
from portality import models
from portality.core import app
from portality.bll.exceptions import NoSuchPropertyException


class AccountCreatedEmail(EventConsumer):
    ID = "account:created:email"

    @classmethod
    def consumes(cls, event):
        return event.id == constants.EVENT_ACCOUNT_CREATED and event.context.get("account") is not None

    @classmethod
    def consume(cls, event):
        context = event.context
        acc = models.Account(**context.get("account"))
        if not acc.reset_token or not acc.email:
            raise NoSuchPropertyException("Account {x} does not have a reset_token and/or an email address".format(x=acc.id))
        cls._send_account_created_email(acc)

    @classmethod
    def _send_account_created_email(cls, account: models.Account):
        # ~~->AccountCreated:Email~~
        forgot_pw_url = app.config.get('BASE_URL', "https://doaj.org") + url_for('account.forgot')
        reset_url = forgot_pw_url

        if account.reset_token is not None:
            reset_url = app.config.get('BASE_URL', "https://doaj.org") + url_for('account.reset', reset_token=account.reset_token)

        password_create_timeout_seconds = int(
            app.config.get("PASSWORD_CREATE_TIMEOUT", app.config.get('PASSWORD_RESET_TIMEOUT', 86400) * 14))
        password_create_timeout_days = int(password_create_timeout_seconds / (60 * 60 * 24))

        to = [account.email]
        fro = app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org')
        subject = app.config.get("SERVICE_NAME", "") + " - account created, please verify your email address"

        # ~~-> Email:Library ~~
        app_email.send_mail(to=to,
                            fro=fro,
                            subject=subject,
                            template_name="email/account_created.jinja2",
                            reset_url=reset_url,
                            email=account.email,
                            timeout_days=password_create_timeout_days,
                            forgot_pw_url=forgot_pw_url
                            )