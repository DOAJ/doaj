from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from doajtest import selenium_helpers
from doajtest.fixtures import AccountFixtureFactory
from doajtest.selenium_helpers import SeleniumTestCase
from portality import models


class LoginSTC(SeleniumTestCase):

    def test_login(self):
        publisher = models.Account(**AccountFixtureFactory.make_publisher_source())
        password = 'password'
        publisher.set_password(password)
        publisher.save(blocking=True)

        selenium_helpers.login(self.selenium, publisher.id, password)
        assert "/login" not in self.selenium.current_url

        target_path = "/publisher/uploadfile"
        selenium_helpers.goto(self.selenium, target_path)
        assert target_path in self.selenium.current_url

    def test_password_toggle_reveals_field(self):
        """
        Regression test: clicking "prefer to use a password?" should
        reveal the password field. It previously did nothing on the
        /apply login page, because that page shared the form markup but
        not the JS that binds the toggle handlers.

        Also checks that the currently-hidden submit button is disabled
        (and the visible one isn't) after each toggle, so a hidden button
        can't be reached via Tab/keyboard while it's out of view.
        """
        selenium_helpers.goto(self.selenium, "/account/login")
        wait = WebDriverWait(self.selenium, 10)

        password_section = wait.until(EC.presence_of_element_located((By.ID, 'password-section')))
        login_link_btn = self.selenium.find_element(By.ID, 'login-link-btn')
        password_btn = self.selenium.find_element(By.ID, 'password-btn')

        assert not password_section.is_displayed()
        assert login_link_btn.get_attribute('disabled') is None
        assert password_btn.get_attribute('disabled') is not None

        self.selenium.find_element(By.ID, 'show-password').click()
        wait.until(EC.visibility_of(password_section))

        assert password_section.is_displayed()
        assert login_link_btn.get_attribute('disabled') is not None
        assert password_btn.get_attribute('disabled') is None

        self.selenium.find_element(By.ID, 'show-login-link').click()
        wait.until(lambda d: not password_section.is_displayed())

        assert login_link_btn.get_attribute('disabled') is None
        assert password_btn.get_attribute('disabled') is not None

    def test_enter_key_logs_in_with_password(self):
        """
        Regression test: after switching to password mode and typing a
        password, pressing Enter must log in with that password - not
        submit a passwordless "send me a login link" request.

        The form always has two submit buttons in the DOM (link and
        password). A browser's native implicit (Enter-key) submission
        targets the *first* submit button in DOM order regardless of
        which is currently visible - disabling the other button doesn't
        change that; a keypress just does nothing once the first button
        in DOM order is disabled. So Enter is handled explicitly by a
        keydown listener on the form (see _login_form_js.html) that
        clicks whichever button is currently visible, instead of relying
        on the browser to resolve the correct default button itself.
        """
        publisher = models.Account(**AccountFixtureFactory.make_publisher_source())
        password = 'password'
        publisher.set_password(password)
        publisher.save(blocking=True)

        selenium_helpers.goto(self.selenium, "/account/login")
        wait = WebDriverWait(self.selenium, 10)

        user_field = wait.until(EC.presence_of_element_located((By.ID, 'user')))
        user_field.send_keys(publisher.email)

        password_section = self.selenium.find_element(By.ID, 'password-section')
        self.selenium.find_element(By.ID, 'show-password').click()
        wait.until(EC.visibility_of(password_section))

        password_field = self.selenium.find_element(By.ID, 'password')
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)

        wait.until(lambda d: "/login" not in d.current_url)
        assert "/login" not in self.selenium.current_url

