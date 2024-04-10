import pytest

from doajtest import selenium_helpers
from doajtest.selenium_helpers import SeleniumTestCase

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from doajtest.fixtures.url_path import URL_APPLY
from doajtest.seleniumtest.application_form.test_fields_common import TestFieldsCommon
from doajtest.seleniumtest.application_form.test_fields_common import Interact
from doajtest.fixtures.messages import ERROR_OA_STATEMENT, ERROR_OA_STATEMENT_URL
from portality import models

from doajtest.fixtures.accounts import create_publisher_a

class ApplicationForm_OACompliance(SeleniumTestCase):

    # go to application page before each test
    def setUp(self):
        super().setUp()
        self.goto_application_page()

    def goto_application_page(self, acc: models.Account = None):
        publisher = acc or create_publisher_a()
        selenium_helpers.login_by_acc(self.selenium, publisher)
        selenium_helpers.goto(self.selenium, URL_APPLY)
        return

    def clickNextButton(self):
        Interact.clickButton(selenium=self.selenium, js_click=self.js_click, button_class_selector="nextBtn",)

    def test_oa_statement(self):
        # self.goto_application_page()
        TestFieldsCommon.find_question(self.selenium, "boai")
        no_radio_button_selector = "#boai-1"
        self.js_click(no_radio_button_selector)
        self.clickNextButton()
        error = TestFieldsCommon.get_error_message(self.selenium, "boai")
        assert error == ERROR_OA_STATEMENT

        yes_radio_button_selector = "#boai-0"
        self.js_click(yes_radio_button_selector)
        self.clickNextButton()
        error = TestFieldsCommon.get_error_message(self.selenium, "boai")
        assert error == None

    # def test_oa_statement_url(self):
    #     TestFieldsCommon.test_if_required_text_or_number_field(field_name="oa_statement_url", error=ERROR_OA_STATEMENT_URL)