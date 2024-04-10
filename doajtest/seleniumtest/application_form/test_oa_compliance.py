import pytest

from doajtest import selenium_helpers
from doajtest.selenium_helpers import SeleniumTestCase

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from doajtest.seleniumtest.application_form.test_application_form_commons import TestFieldsCommon
from doajtest.seleniumtest.application_form.test_application_form_commons import Interactions
from doajtest.fixtures.application_form_error_messages import FixtureMessages
from portality import models


class ApplicationForm_OACompliance(TestFieldsCommon):

    def setUp(self) -> None:
        super().setUp()
        Interactions.goto_application_page(self.selenium);

    def test_oa_statement(self):
        field_name = "boai"
        self.this_radio_button_field_is_required(field_name, FixtureMessages.ERROR_YES_REQUIRED)

        # specific case = "Yes" value required
        self.find_question(field_name)
        no_radio_button_selector = f'#{field_name}-1'
        self.js_click(no_radio_button_selector)
        Interactions.click_next_button(self.js_click)
        error = self.get_error_message(field_name)
        assert error == FixtureMessages.ERROR_OA_STATEMENT

        yes_radio_button_selector = f"#{field_name}-0"
        self.js_click(yes_radio_button_selector)
        Interactions.click_next_button(self.js_click)
        error = self.get_error_message(field_name)
        assert error == None

    def test_oa_statement_url(self):
        field_name = "oa_statement_url"
        self.this_simple_field_is_required(field_name=field_name,
                                           expected_error_value=FixtureMessages.ERROR_OA_STATEMENT_URL)
        self.simple_field_fail(field_name=field_name, value="this_is_not_url", expected_error_value=FixtureMessages.ERROR_INVALID_URL)
        self.simple_field_success(field_name=field_name, value="https://www.test.com")

    def test_oa_start(self):
        field_name = "oa_start"
        self.this_simple_field_is_required(field_name=field_name,
                                           expected_error_value=FixtureMessages.ERROR_OA_START_REQUIRED)
        self.simple_field_fail(field_name=field_name, value="0",
                               expected_error_value=FixtureMessages.ERROR_OA_START_INVALID_VALUE)
        self.simple_field_fail(field_name=field_name, value="9999",
                               expected_error_value=FixtureMessages.ERROR_OA_START_INVALID_VALUE)
        self.simple_field_success(field_name=field_name, value="2020")
