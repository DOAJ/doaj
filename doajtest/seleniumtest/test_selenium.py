from selenium.webdriver.common.by import By

from doajtest.selenium_helpers import SeleniumTestCase


def js_click(driver, selector):
    script = f"document.querySelector('{selector}').click(); "
    driver.execute_script(script)


class PublicPageSTC(SeleniumTestCase):

    def test_search_button(self):
        url = self.get_doaj_url()
        self.selenium.get(url)
        self.selenium.find_element(By.CSS_SELECTOR, '#keywords').send_keys('xxxxx')
        self.selenium.find_element(By.CSS_SELECTOR, 'button[type=submit]').click()
