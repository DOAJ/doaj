import pytest

from doajtest import selenium_helpers
from doajtest.selenium_helpers import SeleniumTestCase

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from doajtest.fixtures.url_path import URL_APPLY
from doajtest.fixtures.messages import ERROR_OA_STATEMENT
from portality import models

from doajtest.fixtures.accounts import create_publisher_a


class ApplicationForm_OACompliance(SeleniumTestCase):
    def goto_application_page(self, acc: models.Account = None):
        publisher = acc or create_publisher_a()
        selenium_helpers.login_by_acc(self.selenium, publisher)
        selenium_helpers.goto(self.selenium, URL_APPLY)
        return

    def clickNext(self):
        next_button_selector = ".nextBtn"
        next_button = self.selenium.find_element(By.CLASS_NAME, 'nextBtn')
        assert next_button
        self.selenium.execute_script("arguments[0].scrollIntoView(true);", next_button)
        self.js_click(next_button_selector)

    def test_oa_statement(self):
        self.goto_application_page()
        oa_statement_question = self.selenium.find_element(By.CLASS_NAME, 'boai__container')
        assert oa_statement_question, "No OA Question container found"
        no_radio_button_selector = "#boai-1"
        self.js_click(no_radio_button_selector)
        self.clickNext()
        xpath_expression = f"//*[contains(text(), '{ERROR_OA_STATEMENT}')]"
        oa_error = self.selenium.find_element(By.XPATH, xpath_expression)
        assert oa_error, "OA error not displayed"

        yes_radio_button_selector = "#boai-0"
        self.js_click(yes_radio_button_selector)
        self.clickNext()
        xpath_expression = f"//*[contains(text(), '{ERROR_OA_STATEMENT}')]"
        with pytest.raises(NoSuchElementException):
            oa_error = self.selenium.find_element(By.XPATH, xpath_expression)
