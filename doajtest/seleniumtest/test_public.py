from doajtest.selenium_helpers import SeleniumTestCase


class PublicSeleniumSTC(SeleniumTestCase):

    def test_public(self):
        self.selenium.get('https://www.google.com/')
        assert self.selenium.page_source
