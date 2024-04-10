import pytest

from doajtest import selenium_helpers
from doajtest.selenium_helpers import SeleniumTestCase

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from doajtest.fixtures.url_path import URL_APPLY
from doajtest.seleniumtest.application_form.test_application_form_commons import TestFieldsCommon
from doajtest.seleniumtest.application_form.test_application_form_commons import Interactions
from doajtest.fixtures.application_form_error_messages import FixtureMessages
from portality import models

from doajtest.fixtures.accounts import create_publisher_a


class ApplicationForm_OACompliance(SeleniumTestCase):

    # go to application page before each test
    def setUp(self):
        super().setUp()
        self.common = TestFieldsCommon(self.selenium, self.js_click)
        self.interact = Interactions(self.selenium, self.js_click)
        self.goto_application_page()

    def goto_application_page(self, acc: models.Account = None):
        publisher = acc or create_publisher_a()
        selenium_helpers.login_by_acc(self.selenium, publisher)
        selenium_helpers.goto(self.selenium, URL_APPLY)
        return

    def test_oa_statement(self):
        field_name = "boai"
        self.common.test_if_required_radio_button_field(field_name,FixtureMessages.ERROR_YES_REQUIRED)

        # specific case = "Yes" value required
        self.common.find_question(field_name)
        no_radio_button_selector = f'#{field_name}-1'
        self.js_click(no_radio_button_selector)
        self.interact.clickNextButton()
        error = self.common.get_error_message(field_name)
        assert error == FixtureMessages.ERROR_OA_STATEMENT

        yes_radio_button_selector = f"#{field_name}-0"
        self.js_click(yes_radio_button_selector)
        self.interact.clickNextButton()
        error = self.common.get_error_message(field_name)
        assert error == None

    def test_oa_statement_url(self):
        field_name = "oa_statement_url"
        self.common.test_if_required_simple_field(field_name=field_name,
                                                  expected_error_value=FixtureMessages.ERROR_OA_STATEMENT_URL)
        self.common.test_error_simple_field(field_name=field_name, value="this_is_not_url", expected_error_value=FixtureMessages.ERROR_INVALID_URL)

    def test_oa_start(self):
        field_name = "oa_start"
        self.common.test_if_required_simple_field(field_name=field_name,
                                                  expected_error_value=FixtureMessages.ERROR_OA_START_REQUIRED)
        self.common.test_error_simple_field(field_name=field_name, value="0",
                                            expected_error_value=FixtureMessages.ERROR_OA_START_INVALID_VALUE)
        self.common.test_error_simple_field(field_name=field_name, value="9999",
                                            expected_error_value=FixtureMessages.ERROR_OA_START_INVALID_VALUE)
