import time
import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock
import random
from datetime import datetime, timedelta

from flask import url_for
from flask_login import current_user

from portality.app import app
from portality.models.account import Account
from portality.core import app as flask_app
from portality.lib import dates

from doajtest.helpers import DoajTestCase


class TestPasswordlessLogin(DoajTestCase):
    def setUp(self):
        super(TestPasswordlessLogin, self).setUp()
        self.ctx = app.test_request_context()
        self.ctx.push()
        self.test_account = Account.make_account(
            username='passwordlessuser',
            name='Passwordless User',
            email='passwordless@example.com',
            roles=['user']
        )
        self.test_account.set_password('password123')
        self.test_account.save()
        self.test_account.refresh()

    def tearDown(self):
        super(TestPasswordlessLogin, self).tearDown()
        Account.remove_by_id(self.test_account.id)
        self.ctx.pop()

    def test_account_set_login_code(self):
        """Test setting and retrieving login code"""
        # Generate a 6-digit code
        code = ''.join(str(random.randint(0, 9)) for _ in range(6))

        # Set login code with default timeout (10 minutes)
        self.test_account.set_login_code(code)
        self.test_account.save()
        self.test_account.refresh()

        # Retrieve the account by the code
        retrieved_account = Account.pull_by_login_code(code)

        # Check the account is retrieved correctly
        self.assertIsNotNone(retrieved_account)
        self.assertEqual(retrieved_account.id, self.test_account.id)
        self.assertEqual(retrieved_account.login_code, code)

        # Check expiry time is set correctly (approximately 10 minutes from now)
        expiry_time = dates.parse(retrieved_account.login_code_expires)
        now = dates.now()
        time_diff = expiry_time - now
        self.assertTrue(timedelta(minutes=9) < time_diff < timedelta(minutes=11))

    def test_login_code_custom_timeout(self):
        """Test setting login code with custom timeout"""
        code = '123456'
        custom_timeout = 1800  # 30 minutes

        self.test_account.set_login_code(code, timeout=custom_timeout)
        self.test_account.save()

        # Check expiry time is set correctly (approximately 30 minutes from now)
        expiry_time = dates.parse(self.test_account.login_code_expires)
        now = dates.now()
        time_diff = expiry_time - now
        self.assertTrue(timedelta(minutes=29) < time_diff < timedelta(minutes=31))

    def test_login_code_validation(self):
        """Test validation of login codes"""
        valid_code = '123456'
        invalid_code = '654321'

        self.test_account.set_login_code(valid_code)
        self.test_account.save()

        # Test with correct code
        self.assertTrue(self.test_account.is_login_code_valid(valid_code))

        # Test with incorrect code
        self.assertFalse(self.test_account.is_login_code_valid(invalid_code))

        # Test with no code in account
        another_account = Account.make_account(
            username='nologincode',
            name='No Login Code',
            email='nocode@example.com'
        )
        self.assertFalse(another_account.is_login_code_valid(valid_code))

        # Clean up
        Account.remove_by_id(another_account.id)

    def test_login_code_expiry(self):
        """Test login code expiry"""
        code = '123456'

        # Set a code with a very short timeout (1 second)
        self.test_account.set_login_code(code, timeout=1)
        self.test_account.save()

        # Code should be valid initially
        self.assertTrue(self.test_account.is_login_code_valid(code))

        # Wait for the code to expire
        time.sleep(2)

        # Code should now be invalid due to expiry
        self.assertFalse(self.test_account.is_login_code_valid(code))

    def test_remove_login_code(self):
        """Test removing login code"""
        code = '123456'

        self.test_account.set_login_code(code)
        self.test_account.save()

        # Verify code exists
        self.assertEqual(self.test_account.login_code, code)

        # Remove the code
        self.test_account.remove_login_code()
        self.test_account.save()

        # Verify code is removed
        self.assertIsNone(self.test_account.login_code)
        self.assertIsNone(self.test_account.login_code_expires)

        # Verify validation fails after removal
        self.assertFalse(self.test_account.is_login_code_valid(code))


@patch('portality.view.account.send_login_code_email')
class TestPasswordlessLoginEndpoints(DoajTestCase):
    def setUp(self):
        super(TestPasswordlessLoginEndpoints, self).setUp()
        self.app = app.test_client()
        self.app.testing = True

        # Create a test account
        self.test_account = Account.make_account(
            username='passuser',
            name='Password User',
            email='pass@example.com',
            roles=['user']
        )
        self.test_account.set_password('userpass')
        self.test_account.save()
        self.test_account.refresh()

    def tearDown(self):
        super(TestPasswordlessLoginEndpoints, self).tearDown()
        Account.remove_by_id(self.test_account.id)

    def test_login_get_link_request(self, mock_send_email):
        """Test requesting a login link"""
        # Set up mock
        mock_send_email.return_value = None

        # Make the request
        response = self.app.post('/account/login', data={
            'user': 'pass@example.com',
            'action': 'get_link'
        }, follow_redirects=True)

        # Check that email was sent
        self.assertEqual(mock_send_email.call_count, 1)
        args, kwargs = mock_send_email.call_args
        sent_email, code = args
        self.assertEqual(sent_email, self.test_account.email)
        self.assertEqual(len(code), 6)  # 6-digit code

        # Verify code was stored in the account
        account = Account.pull(self.test_account.id)
        self.assertEqual(account.login_code, code)

        # Check the response includes the verification form
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'verification code', response.data)

    def test_verify_code_success(self, mock_send_email):
        """Test successful verification of login code"""
        # Set a login code
        code = '123456'
        self.test_account.set_login_code(code)
        self.test_account.save()
        self.test_account.refresh()

        # Make the verification request
        response = self.app.post('/account/verify-code', data={
            'email': 'pass@example.com',
            'code': code
        }, follow_redirects=True)

        # Verify successful login
        self.assertEqual(response.status_code, 200)

        # Verify code was removed
        account = Account.pull(self.test_account.id)
        account.refresh()
        self.assertIsNone(account.login_code)

    def test_verify_code_invalid(self, mock_send_email):
        """Test invalid login code verification"""
        # Set a login code
        code = '123456'
        self.test_account.set_login_code(code)
        self.test_account.save()
        self.test_account.refresh()

        # Make the verification request with wrong code
        response = self.app.post('/account/verify-code', data={
            'email': 'pass@example.com',
            'code': '999999'  # Wrong code
        }, follow_redirects=True)

        # Check for error message
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid or expired verification code', response.data)

        # Verify code was not removed
        account = Account.pull(self.test_account.id)
        self.assertEqual(account.login_code, code)

    def test_verify_code_expired(self, mock_send_email):
        """Test expired login code verification"""
        # Set a login code with expiry in the past
        code = '123456'
        self.test_account.set_login_code(code, timeout=1)
        self.test_account.save()

        # Wait for code to expire
        time.sleep(2)

        # Make the verification request
        response = self.app.post('/account/verify-code', data={
            'email': 'pass@example.com',
            'code': code
        }, follow_redirects=True)

        # Check for error message
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid or expired verification code', response.data)

    def test_login_nonexistent_account(self, mock_send_email):
        """Test requesting a login link for non-existent account"""
        # Make the request with non-existent email
        response = self.app.post('/account/login', data={
            'user': 'nonexistent@example.com',
            'action': 'get_link'
        }, follow_redirects=True)

        # Check that email was not sent
        mock_send_email.assert_not_called()

        # Check for generic message that doesn't reveal if account exists
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Account not recognised', response.data)

    def test_password_login_still_works(self, mock_send_email):
        """Test that traditional password login still works"""
        # Make a traditional login request
        response = self.app.post('/account/login', data={
            'user': 'pass@example.com',
            'password': 'userpass',
            'action': 'password_login'
        }, follow_redirects=True)

        # Check successful login
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back', response.data)

    def test_login_form_validation(self, mock_send_email):
        """Test form validation for login"""
        # Test with missing email
        response = self.app.post('/account/login', data={
            'action': 'get_link'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'This field is required', response.data)

        # Test with invalid email format
        response = self.app.post('/account/login', data={
            'user': 'not-an-email',
            'action': 'get_link'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Account not recognised', response.data)


class TestSendLoginCodeEmail(TestCase):
    @patch('portality.view.account.send_mail')
    def test_send_login_code_email(self, mock_send_mail):
        """Test the send_login_code_email function"""
        with app.test_request_context():
            email = 'test@example.com'
            code = '123456'

            # Call the function
            from portality.view.account import send_login_code_email
            send_login_code_email(email, code)

            # Check email was sent with correct parameters
            mock_send_mail.assert_called_once()

            # Verify parameters
            args, kwargs = mock_send_mail.call_args
            self.assertEqual(kwargs['to'], [email])
            self.assertEqual(kwargs['code'], code)
            self.assertIn('login_url', kwargs)
            self.assertEqual(kwargs['expiry_minutes'], 10)
