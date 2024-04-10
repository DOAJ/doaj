from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from doajtest import selenium_helpers
from doajtest.selenium_helpers import SeleniumTestCase
from portality import models
from doajtest.fixtures.accounts import create_publisher_a
from doajtest.fixtures.url_path import URL_APPLY


class Interactions():

    @classmethod
    def click_next_button(self, js_click):
        js_click(selector=".nextBtn")

    @classmethod
    def goto_application_page(self, driver: 'WebDriver', acc: models.Account = None):
        publisher = acc or create_publisher_a()
        selenium_helpers.login_by_acc(driver, publisher)
        selenium_helpers.goto(driver, URL_APPLY)
        return

    @classmethod
    def goto_to_section(self, js_click, section_number):
        js_click(f"#page_link-{section_number}");


SIMPLE_FIELDS_TYPES = ["text", "number", "url"]


class TestFieldsCommon(SeleniumTestCase):

    def setUp(self):
        super().setUp()

    def find_question(self, field_name):
        question = self.selenium.find_element(By.CLASS_NAME, f'{field_name}__container');
        assert question, f'{field_name} question container not found'
        return question

    def get_error_message(self, field_name):
        error_div_id = f"{field_name}_checkbox-errors"
        error_xpath = f"//div[@id='{error_div_id}']/ul/li/p/small"
        parsley_error_xpath = f"//div[@id='{error_div_id}']/ul/li[@class='parsley-type']"

        try:
            # Check for custom error message
            error_element = WebDriverWait(self.selenium, 1).until(
                EC.visibility_of_element_located((By.XPATH, error_xpath))
            )
        except TimeoutException:
            try:
                # check for parsley general error message if custom is not displayed
                error_element = WebDriverWait(self.selenium, 1).until(
                    EC.visibility_of_element_located((By.XPATH, parsley_error_xpath))
                )
            except TimeoutException:
                return None

        if error_element.is_displayed():
            return error_element.text.strip()
        else:
            return None

    def required_simple_field(self, field_name, expected_error_value=None):
        # Step 1: Find the question with "field_name"
        question = self.find_question(field_name)
        assert question is not None, f"Question with field name '{field_name}' not found"

        # Step 2: Assure the value = ""
        # Assuming 'value' is a direct child of the question element
        input_element = question.find_element(By.CSS_SELECTOR, 'input')
        self.selenium.execute_script("arguments[0].scrollIntoView(true);", input_element)
        WebDriverWait(self.selenium, 1).until(EC.visibility_of(input_element))

        input_type = input_element.get_attribute('type')
        if input_type in SIMPLE_FIELDS_TYPES:
            input_element.clear()
        else:
            raise ValueError(
                f"Unexpected input type '{input_type}' for field '{field_name}'. Expected 'text' or 'number'.")

        assert input_element.get_attribute('required') is not None, f"Field '{field_name}' is not marked as required"

        Interactions.click_next_button(self.js_click)

        # Step 4: Assure the required error exists
        error_message = self.get_error_message(field_name)
        assert error_message is not None, f"Required error for field '{field_name}' not displayed"

        # Step 5: Compare the error value to the provided value (optional)
        if expected_error_value is not None:
            assert error_message == expected_error_value, \
                f"Error message for field '{field_name}' does not match expected value"

    def add_value_to_simple_field(self, field_name, value):
        # Step 1: Find the question with "field_name"
        question = self.find_question(field_name)
        assert question is not None, f"Question with field name '{field_name}' not found"

        input_element = question.find_element(By.CSS_SELECTOR, 'input')
        self.selenium.execute_script("arguments[0].scrollIntoView(true);", input_element)
        WebDriverWait(self.selenium, 1).until(EC.visibility_of(input_element))

        input_type = input_element.get_attribute('type')
        if input_type in SIMPLE_FIELDS_TYPES:
            input_element.send_keys(value)
        else:
            raise ValueError(
                f"Unexpected input type '{input_type}' for field '{field_name}'. Expected 'text' or 'number'.")

    def clear_simple_field(self, field_name):
        question = self.find_question(field_name)
        assert question is not None, f"Question with field name '{field_name}' not found"

        input_element = question.find_element(By.CSS_SELECTOR, 'input')
        self.selenium.execute_script("arguments[0].scrollIntoView(true);", input_element)
        WebDriverWait(self.selenium, 1).until(EC.visibility_of(input_element))

        input_type = input_element.get_attribute('type')
        if input_type in SIMPLE_FIELDS_TYPES:
            input_element.clear()
        else:
            raise ValueError(
                f"Unexpected input type '{input_type}' for field '{field_name}'. Expected 'text' or 'number'.")

    def simple_field_failed(self, field_name, value, expected_error_value=None):
        self.add_value_to_simple_field(field_name, value)
        Interactions.click_next_button(self.js_click)
        error_message = self.get_error_message(field_name)
        assert error_message is not None, f"Required error for field '{field_name}' not displayed"

        if expected_error_value is not None:
            assert error_message == expected_error_value, \
                f"Error message for field '{field_name}' does not match expected value"
        self.clear_simple_field(field_name)

    def simple_field_success(self, field_name, value):
        self.add_value_to_simple_field(field_name, value)
        Interactions.click_next_button(self.js_click)
        error_message = self.get_error_message(field_name)
        assert error_message is None
        self.clear_simple_field(field_name)


    def required_radio_button_field(self, field_name, expected_error_value=None):
        question_container = self.find_question(field_name)

        # Check if the question is marked as required
        first_ul = question_container.find_element(By.CSS_SELECTOR, "ul")
        is_required = first_ul.get_attribute("required")
        assert is_required is not None, "Question should be marked as required"

        # Find hidden radio buttons using JavaScript
        radio_buttons = self.selenium.execute_script(
            f"return document.querySelectorAll('input[name={field_name}]');"
        )

        # Unselect all radio buttons using JavaScript
        for radio_button in radio_buttons:
            self.selenium.execute_script("arguments[0].checked = false;", radio_button)

        Interactions.click_next_button(self.js_click)
        error = self.get_error_message(field_name)
        assert error == expected_error_value
