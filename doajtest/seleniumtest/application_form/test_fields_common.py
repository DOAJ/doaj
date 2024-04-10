from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class Interact():

    @classmethod
    def clickButton(cls, selenium, js_click, button_class_selector=None, button_id_selector=None):
        next_button = selenium.find_element(By.CLASS_NAME, button_class_selector if button_class_selector else button_id_selector)
        assert next_button
        selenium.execute_script("arguments[0].scrollIntoView(true);", next_button)
        if button_class_selector:
            js_click(f'.{button_class_selector}')
        elif button_id_selector:
            js_click(f'#{button_id_selector}')
        else:
            raise ValueError("Either 'button_class_selector' or 'button_id_selector' must be provided")


class TestFieldsCommon():

    @classmethod
    def find_question(cls, selenium, field_name):
        question = selenium.find_element(By.CLASS_NAME, f'{field_name}__container');
        assert question, f'{field_name} question container not found'
        return question

    @classmethod
    def get_error_message(cls, selenium, field_name):
        error_div_id = f"{field_name}_checkbox-errors"
        error_xpath = f"//div[@id='{error_div_id}']/ul/li/p/small"

        try:
            error_element = WebDriverWait(selenium, 1).until(
                EC.presence_of_element_located((By.XPATH, error_xpath))
            )
            if error_element.is_displayed():
                return error_element.text.strip()
            else:
                return None
        except TimeoutException:
            return None

    @classmethod
    def test_if_required_text_or_number_field(self, field_name, expected_error_value=None):
        # Step 1: Find the question with "field_name"
        question = self.find_question(field_name)
        assert question is not None, f"Question with field name '{field_name}' not found"

        # Step 2: Assure the value = ""
        # Assuming 'value' is a direct child of the question element
        input_element = question.find_element(By.CSS_SELECTOR, 'input')
        input_type = input_element.get_attribute('type')
        if input_type == 'text' or input_type == 'number':
            input_element.clear()
        else:
            raise ValueError(
                f"Unexpected input type '{input_type}' for field '{field_name}'. Expected 'text' or 'number'.")

        assert input_element.get_attribute('required') is not None, f"Field '{field_name}' is not marked as required"

        # Step 3: Click Next Button
        self.clickNextButton()

        # Step 4: Assure the required error exists
        error_message = self.get_error_message(field_name)
        assert error_message is not None, f"Required error for field '{field_name}' not displayed"

        # Step 5: Compare the error value to the provided value (optional)
        if expected_error_value is not None:
            assert error_message == expected_error_value, \
                f"Error message for field '{field_name}' does not match expected value"
