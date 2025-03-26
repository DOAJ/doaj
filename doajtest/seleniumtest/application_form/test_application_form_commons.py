from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from doajtest import selenium_helpers
from doajtest.selenium_helpers import SeleniumTestCase
from portality import models
from doajtest.fixtures.accounts import create_publisher_a
from doajtest.fixtures.url_path import URL_APPLY

TIMEOUT = 1;
class Interactions():

    @classmethod
    def click_next_button(cls, driver, js_click):
        js_click(selector=".nextBtn")
        selenium_helpers.wait_for(driver, TIMEOUT)

    @classmethod
    def goto_application_page(cls, driver: 'WebDriver', acc: models.Account = None):
        publisher = acc or create_publisher_a()
        selenium_helpers.login_by_acc(driver, publisher)
        selenium_helpers.goto(driver, URL_APPLY)
        selenium_helpers.wait_for(driver, TIMEOUT)

    @classmethod
    def goto_section(cls, driver, js_click, section_number):
        js_click(f"#page_link-{section_number}");
        selenium_helpers.wait_for(driver, TIMEOUT)


SIMPLE_FIELDS_TYPES = ["text", "number", "url"]


class TestFieldsCommon(SeleniumTestCase):

    def setUp(self):
        super().setUp()

    def find_question(self, field_name):
        question = self.selenium.find_element(By.CLASS_NAME, f'{field_name}__container');
        assert question, f'{field_name} question container not found'
        return question

    def find_hidden_element(self, field_id):
        element = self.selenium.execute_script(
            f"return document.getElementById('{field_id}');"
        )
        assert element is not None;
        return element;

    def find_main_input_in_question(self, question, scroll_into=True):
        input_element = question.find_element(By.CSS_SELECTOR, 'input')
        assert input_element is not None

        if (scroll_into):
            self.selenium.execute_script("arguments[0].scrollIntoView(true);", question)
            WebDriverWait(self.selenium, 1).until(EC.visibility_of(question))

        return input_element

    def get_error_message(self, field_name):
        error_div_id = f"{field_name}_checkbox-errors"
        error_xpath = f"//div[@id='{error_div_id}']/ul/li/p/small"
        parsley_error_xpath = f"//div[@id='{error_div_id}']/ul/li[starts-with(@class, 'parsley-')]"

        try:
            # Check for custom error message
            error_element = self.selenium.find_element(By.XPATH, error_xpath)
        except NoSuchElementException:
            try:
                # check for parsley general error message if custom is not displayed
                error_element = self.selenium.find_element(By.XPATH, parsley_error_xpath)
            except NoSuchElementException:
                return None

        if error_element.is_displayed():
            return error_element.text.strip()
        else:
            return None

    def check_error_msg(self, field_name, expected_error_value):
        error_message = self.get_error_message(field_name)
        assert error_message is not None, f"Required error for field '{field_name}' not displayed"

        # Step 5: Compare the error value to the provided value (optional)
        if expected_error_value is not None:
            assert error_message == expected_error_value, \
                f"Error message for field '{field_name}' does not match expected value"

    def check_if_simple_input(self, field_name, input):
        input_type = input.get_attribute("type");
        if input_type not in SIMPLE_FIELDS_TYPES:
            raise ValueError(
                f"Unexpected input type '{input_type}' for field '{field_name}'. Expected 'text' or 'number'.")

    def this_field_is_required(self, field_name, field_id=None, expected_error_value=None, is_select2=False):
        question = self.find_question(field_name)

        main_input = self.find_main_input_in_question(question);
        if (is_select2):
            input_element = self.find_hidden_element(field_name);
            assert input_element.get_attribute(
                'required') is not None, f"Field '{field_name}' is not marked as required"
        else:
            assert main_input.get_attribute('required') is not None, f"Field '{field_name}' is not marked as required"

        Interactions.click_next_button(self.selenium, self.js_click)

        self.check_error_msg(field_name, expected_error_value)

    def this_simple_field_is_optional(self, field_name):
        question = self.find_question(field_name)

        input_element = self.find_main_input_in_question(question);

        input_type = input_element.get_attribute('type');
        self.clear_simple_field(field_name);

        # Step 4: Assure the required error exists
        error_message = self.get_error_message(field_name)
        assert error_message is None, f"Field '{field_name}' should be optional"

    def add_value_to_simple_field(self, field_name, value):
        # Step 1: Find the question with "field_name"
        question = self.find_question(field_name)
        input_element = self.find_main_input_in_question(question);
        input_type = input_element.get_attribute('type')
        self.clear_simple_field(field_name);
        input_element.send_keys(value);

    def clear_simple_field(self, field_name):
        question = self.find_question(field_name)
        input_element = self.find_main_input_in_question(question);
        self.check_if_simple_input(field_name, input_element);
        input_element.clear();


    def simple_field_fail(self, field_name, value, expected_error_value=None):
        self.add_value_to_simple_field(field_name, value)
        Interactions.click_next_button(self.selenium, self.js_click)
        self.check_error_msg(field_name, expected_error_value)

    def simple_field_success(self, field_name, value):
        self.add_value_to_simple_field(field_name, value)
        Interactions.click_next_button(self.selenium, self.js_click)
        error_message = self.get_error_message(field_name)
        assert error_message is None

    def this_radio_button_field_is_required(self, field_name, expected_error_value=None):
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

        Interactions.click_next_button(self.selenium, self.js_click)
        self.check_error_msg(field_name, expected_error_value)

    def this_field_is_optional_if(self, field_name, optional_if_field_name, optional_if_value, expected_error_value):
        self.clear_simple_field(field_name);
        self.clear_simple_field(optional_if_field_name);
        Interactions.click_next_button(self.selenium, self.js_click)
        self.check_error_msg(field_name, expected_error_value)
        self.add_value_to_simple_field(optional_if_field_name, optional_if_value);
        Interactions.click_next_button(self.selenium, self.js_click)
        self.this_simple_field_is_optional(field_name);

    def these_field_must_be_different_than(self, field_name, different_than_field, correct_value, expected_error_value):
        self.add_value_to_simple_field(different_than_field, correct_value);
        self.add_value_to_simple_field(field_name, correct_value);
        Interactions.click_next_button(self.selenium, self.js_click)
        self.check_error_msg(field_name, expected_error_value)

    def select2_tags(self, field_name, correct_value, incorrect_value=None, limit=None, hint=None, min_chars=None, separator=None):
        select2_results_id = "select2-results"
        # make sure that if limit is not None then incorrect_value is not None either
        if limit is not None and incorrect_value is None:
            raise ValueError(
                f"If you provide limit, you need to provide incorrect value.")
        # find question and input
        question = self.find_question(field_name=field_name);
        input = self.find_main_input_in_question(question);

        # test whether focus shows the dropdown
        input.send_keys("");
        dropdown = self.find_hidden_element(select2_results_id);
        assert dropdown is not None

        #if the hint is not None, check the hint
        if hint is not None:
            dropdown.find_element(By.TAG_NAME, "li");
            assert dropdown.text == hint

        # test whether input shows dropdown; if min_chars - whether shows after len(input) >= min_chars

        # test choosing an option from the list

        # test adding string with limiters - correct value

        # if limit is not None - add incorrect value, test limit message

        # unfocus - see if value has correct length (over limit tags not added in the previous step)
        pass
