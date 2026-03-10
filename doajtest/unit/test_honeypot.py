from doajtest.helpers import DoajTestCase
from doajtest.fixtures import registrationForm
from portality.view.account import RegisterForm

class TestHoneypot(DoajTestCase):

    def setUp(self):
        pass

    def test_01_valid_form_with_valid_honeypot(self):
        valid_form = RegisterForm(registrationForm.create_valid_form_with_valid_honeypot())
        assert valid_form.is_bot() is False, "Test failed: The form should not be identified as a bot."

    def test_02_valid_form_with_invalid_honeypot_timer_exceeds(self):
        valid_form = RegisterForm(registrationForm.create_valid_form_with_invalid_honeypot_timer_exceeds())
        assert valid_form.is_bot() is True, "Test failed: The form should be identified as a bot due to honeypot timer exceeding threshold."

    def test_03_valid_form_with_invalid_honeypot_email_not_empty(self):
        valid_form = RegisterForm(registrationForm.create_valid_form_with_invalid_honeypot_email_not_empty())
        assert valid_form.is_bot() is True, "Test failed: The form should be identified as a bot due to honeypot email field not being empty."

    def test_04_invalid_form_with_valid_honeypot(self):
        invalid_form = RegisterForm(registrationForm.create_invalid_form_with_valid_honeypot())
        assert invalid_form.is_bot() is False, "Test failed: The form should not be identified as a bot since honeypot is valid."

    def test_05_invalid_form_with_invalid_honeypot_timer_exceeds(self):
        invalid_form = RegisterForm(registrationForm.create_invalid_form_with_invalid_honeypot_timer_exceeds())
        assert invalid_form.is_bot() is True, "Test failed: The form should be identified as a bot due to honeypot timer exceeding threshold."

    def test_06_invalid_form_with_invalid_honeypot_email_not_empty(self):
        invalid_form = RegisterForm(registrationForm.create_invalid_form_with_invalid_honeypot_email_not_empty())
        assert invalid_form.is_bot() is True, "Test failed: The form should be identified as a bot due to honeypot email field not being empty."

    def test_07_valid_form_with_invalid_honeypot_both_fields(self):
        valid_form = RegisterForm(registrationForm.create_valid_form_with_invalid_honeypot_both_fields())
        assert valid_form.is_bot() is True, "Test failed: The form should be identified as a bot due to both honeypot fields being invalid."

    def test_08_invalid_form_with_invalid_honeypot_both_fields(self):
        invalid_form = RegisterForm(registrationForm.create_invalid_form_with_invalid_honeypot_both_fields())
        assert invalid_form.is_bot() is True, "Test failed: The form should be identified as a bot due to both honeypot fields being invalid."