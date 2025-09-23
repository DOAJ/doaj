from typing import Optional, Tuple

from portality.core import app
from portality.models import Account
from portality.bll import exceptions
from portality.lib.security import Encryption

class AccountService:
    """Business logic for account login verification."""

    def parse_login_token(self, encrypted_token: Optional[str]) -> dict:
        """Decrypt token to params; return {} on failure or if not provided."""
        if not encrypted_token:
            return {}
        enc = Encryption(app.config.get('PASSWORDLESS_ENCRYPTION_KEY'))
        return enc.decrypt_params(encrypted_token) or {}

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