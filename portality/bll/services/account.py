from typing import Optional, Tuple
import random

from flask import url_for

from portality.core import app
from portality.models import Account
from portality.bll import exceptions
from portality.lib.security import Encryption
from portality.app_email import send_mail
from portality.ui import templates

class AccountService:
    """Business logic for account login and verification."""

    # Defaults for passwordless login code
    LOGIN_CODE_LENGTH = 6
    LOGIN_CODE_TIMEOUT = 600  # seconds (10 minutes)

    def resolve_user(self, username: str) -> Optional[Account]:
        """Resolve a user by account id or email, depending on config."""
        if username is None or username == "":
            return None
        if app.config.get('LOGIN_VIA_ACCOUNT_ID', False):
            return Account.pull(username) or Account.pull_by_email(username)
        return Account.pull_by_email(username)

    def initiate_login_code(self, user: Account) -> str:
        """Generate and persist a passwordless login code for the user; return the code."""
        if user is None or user.email is None:
            raise exceptions.ArgumentException("User account is not available for login code.")
        code = ''.join(str(random.randint(0, 9)) for _ in range(self.LOGIN_CODE_LENGTH))
        user.set_login_code(code, timeout=self.LOGIN_CODE_TIMEOUT)
        user.save()
        return code

    def send_login_code_email(self, user: Account, code: str, redirected: Optional[str] = "") -> None:
        """Compose and send the passwordless login email with code and a direct link.
        """
        if user is None or not user.email:
            raise exceptions.ArgumentException("Cannot send login code email: user/email missing")

        params = {"email": user.email, "code": code}
        if redirected:
            params["redirected"] = redirected

        login_url = None
        try:
            encrypted = Encryption(app.config.get('PASSWORDLESS_ENCRYPTION_KEY')).encrypt_params(params)
            login_url = url_for('account.verify_code', token=encrypted, _external=True)
        except (ValueError, TypeError, Exception) as e:
            # login_url is mandatory; propagate as an argument/config problem
            app.logger.error(f"Failed to create encrypted login URL: {e.__class__.__name__}: {str(e)}")
            raise exceptions.ArgumentException("Invalid encryption key or login url creation error")

        send_mail(
            to=[user.email],
            fro=app.config.get('SYSTEM_EMAIL_FROM'),
            html_body_flag=True,
            subject="Your Login Code for DOAJ",
            template_name=templates.EMAIL_LOGIN_LINK,
            plaintext_template_name=templates.EMAIL_LOGIN_LINK_PLAINTEXT,
            code=code,
            login_url=login_url,
            expiry_minutes=10
        )

    def verify_password_login(self, user: Account, password: Optional[str]) -> Account:
        """
        Check the user's password.
        Raises IllegalStatusException('no_password') if no password set.
        Raises IllegalStatusException('incorrect_password') if password does not match.
        Returns the user on success.
        """
        if user is None:
            raise exceptions.NoSuchObjectException("Account not recognised.")
        try:
            if user.check_password(password):
                return user
            # wrong password
            raise exceptions.IllegalStatusException("incorrect_password")
        except KeyError:
            # account has no password set
            raise exceptions.IllegalStatusException("no_password")

    def parse_login_token(self, encrypted_token: Optional[str]) -> dict:
        """Decrypt token to params; raise ArgumentException on failure or if not provided."""
        if not encrypted_token:
            raise exceptions.ArgumentException("login token is required")
        try:
            enc = Encryption(app.config.get('PASSWORDLESS_ENCRYPTION_KEY'))
            params = enc.decrypt_params(encrypted_token) or {}
        except ValueError as e:
            app.logger.error(f"Invalid encryption key: {e.__class__.__name__}: {str(e)}")
            raise exceptions.ArgumentException("Invalid encryption key")
        if not isinstance(params, dict) or not params:
            raise exceptions.ArgumentException("invalid login token")
        return params

    def verify_login_code(
        self,
        *,
        encrypted_token: Optional[str] = None,
        email: Optional[str] = None,
        code: Optional[str] = None,
    ) -> Tuple[Account, Optional[str]]:
        """
        Verify a login either from an encrypted token or plain email/code.

        Returns: (account, redirected)
        Raises:
            - exceptions.ArgumentException if params missing
            - exceptions.NoSuchObjectException if account not found
            - exceptions.IllegalStatusException if code invalid/expired
        """
        params = {}
        if encrypted_token:
            params = self.parse_login_token(encrypted_token)
            tok_email = params.get('email')
            tok_code = params.get('code')
            redirected = params.get('redirected')
        else:
            tok_email = email
            tok_code = code
            redirected = None

        if not tok_email or not tok_code:
            raise exceptions.ArgumentException("Required parameters not available.")

        account = Account.pull_by_email(tok_email)
        if not account:
            raise exceptions.NoSuchObjectException("Account not recognised.")

        if not account.is_login_code_valid(tok_code):
            raise exceptions.IllegalStatusException("Invalid or expired verification code")

        # Business state change: clear and persist the code
        account.remove_login_code()
        account.save()

        return account, redirected