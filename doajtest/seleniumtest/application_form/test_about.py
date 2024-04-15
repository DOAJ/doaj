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


class ApplicationForm_About(TestFieldsCommon):

    # go to application page before each test
    def setUp(self):
        super().setUp()
        Interactions.goto_application_page(self.selenium)
        Interactions.goto_section(self.selenium, self.js_click, 1);


    def test_title(self):
        field_name="title"
        self.this_simple_field_is_required(field_name=field_name)
        self.simple_field_success(field_name=field_name, value="Serendipity Science: Accidental Alchemy & Quantum Quirks")

    def test_alternative_title(self):
        field_name="alternative_title"
        self.this_simple_field_is_optional(field_name=field_name)
        self.simple_field_success(field_name, value="The Absurd Chronicles of Science: From Alchemy to Mischief")

    def test_journal_url(self):
        field_name="journal_url"
        self.this_simple_field_is_required(field_name=field_name, expected_error_value=FixtureMessages.ERROR_JOURNAL_URL_REQUIRED)
        self.simple_field_fail(field_name=field_name, value="incorect_url", expected_error_value=FixtureMessages.ERROR_JOURNAL_URL_INVALID)
        self.simple_field_success(field_name=field_name, value="https://www.absurdChronicles.com")