from doajtest import selenium_helpers
from doajtest.selenium_helpers import SeleniumTestCase


class CicleciSTC(SeleniumTestCase):

    def test_public(self):
        self.selenium.get(self.get_doaj_url())
        print(self.selenium.page_source)
        assert self.selenium.page_source

    def test_goto(self):
        selenium_helpers.goto(self.selenium, "/login")
