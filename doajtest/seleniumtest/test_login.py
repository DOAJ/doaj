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

