from unittest.mock import patch

from portality.app import app
from portality.models.account import Account
from doajtest.fixtures.accounts import AccountFixtureFactory

from doajtest.helpers import DoajTestCase

# The account blueprint is registered twice - once at /account, and once
# locale-prefixed at /<lang>/account (name "locale_account"). Both must
# behave the same way.
LOGIN_ROUTES = ('/account/login', '/en/account/login', '/fr/account/login')


class TestAccountLogin(DoajTestCase):

    def setUp(self):
        super().setUp()
        self.app_client = app.test_client()
        self.app_client.testing = True
        self.test_account = Account(**AccountFixtureFactory.make_publisher_source())
        self.test_account.set_password('correct-password')
        self.test_account.save(blocking=True)

    def tearDown(self):
        self.app_client.get('/account/logout', follow_redirects=True)
        super().tearDown()

    def test_01_correct_password_logs_in(self):
        """ Use test client to fill the login form with correct password for all login routes"""
        for route in LOGIN_ROUTES:
            with self.subTest(route=route):
                resp = self.app_client.post(route, data=dict(
                    user=self.test_account.email, password='correct-password', action='password_login'
                ), follow_redirects=True)
                self.assertEqual(resp.status_code, 200)
                self.assertIn(b'Welcome back', resp.data)
                self.app_client.get('/account/logout', follow_redirects=True)

    def test_02_incorrect_password_shows_error_not_500(self):
        """
        Regression test: an incorrect password used to 500 when the
        request went via the locale-prefixed route, because the handler
        builds a "reset your password" link with a relative
        url_for('.forgot'), and the blueprint's url_value_preprocessor
        stripped 'lang' from request.view_args before that call runs - so
        Flask has no value to fill in for the 'lang' that the
        locale_account.forgot rule requires, and url_for raises a
        werkzeug BuildError.
        """
        for route in LOGIN_ROUTES:
            with self.subTest(route=route):
                resp = self.app_client.post(route, data=dict(
                    user=self.test_account.email, password='wrong-password', action='password_login'
                ), follow_redirects=True)
                self.assertEqual(resp.status_code, 200)
                self.assertIn(b'password you entered is incorrect', resp.data)

    def test_03_unrecognised_account(self):
        """ Check the message reaches the frontend when the account isn't found"""
        for route in LOGIN_ROUTES:
            with self.subTest(route=route):
                resp = self.app_client.post(route, data=dict(
                    user='doesnotexist@example.com', password='whatever', action='password_login'
                ), follow_redirects=True)
                self.assertEqual(resp.status_code, 200)
                self.assertIn(b'Account not recognised', resp.data)

    @patch('portality.bll.services.account.AccountService.send_login_code_email')
    def test_04_passwordless_request_link(self, mock_send_email):
        """
        Each login route needs its own account/email: the passwordless resend
        backoff (PWLESS_RESEND_MIN_INTERVAL) would otherwise block the
        2nd and 3rd requests for the same email fired straight after
        the first, which has nothing to do with what's under test here.
        """
        #
        for i, route in enumerate(LOGIN_ROUTES):
            with self.subTest(route=route):
                mock_send_email.reset_mock()
                email = f'pwless{i}@example.com'
                account = Account.make_account(
                    username=f'pwlessuser{i}', name='Passwordless User', email=email, roles=['user']
                )
                account.set_password('correct-password')
                account.save()
                account.refresh()

                resp = self.app_client.post(route, data=dict(
                    user=email, action='get_link'
                ), follow_redirects=True)
                self.assertEqual(resp.status_code, 200)
                mock_send_email.assert_called_once()

    def test_05_apply_redirect_login_includes_password_toggle_script(self):
        """
        Regression test: /account/login?redirected=apply renders the
        login_to_apply template, which shares the login form markup
        (including the "Prefer to use a password?" link) with the plain
        login page via _login_form.html, but didn't carry over the JS
        that binds the toggle click handler - so on the apply flow the
        link was inert and never revealed the password field, even
        though it worked fine on the plain /login page.
        """
        for route in LOGIN_ROUTES:
            with self.subTest(route=route):
                plain_resp = self.app_client.get(route, follow_redirects=True)
                apply_resp = self.app_client.get(f'{route}?redirected=apply', follow_redirects=True)

                for resp in (plain_resp, apply_resp):
                    self.assertEqual(resp.status_code, 200)
                    # the toggle link/markup should be present on both...
                    self.assertIn(b'id="show-password"', resp.data)
                    # ...and so should the script that makes it work
                    self.assertIn(b"$('#show-password').on('click'", resp.data)
