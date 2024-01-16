from doajtest.selenium_helpers import SeleniumTestCase


class PublicSeleniumSTC(SeleniumTestCase):

    def test_google(self):
        self.selenium.get('https://www.google.com/')
        print(self.selenium.page_source)
        assert self.selenium.page_source
