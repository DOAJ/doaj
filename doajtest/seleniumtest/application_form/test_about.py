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


class ApplicationForm_OACompliance(SeleniumTestCase):

    # go to application page before each test
    def setUp(self):
        super().setUp()
        self.common = TestFieldsCommon(self.selenium, self.js_click)
        self.interact = Interactions(self.selenium, self.js_click)
        self.interact.goto_application_page()


    def test_oa_statement(self):
