from doajtest.helpers import DoajTestCase
from portality.view.forms import ContactUs
from portality.app_email import send_contact_form

class TestContact(DoajTestCase):

    def setUp(self):
        super(TestContact, self).setUp()

    def tearDown(self):
        super(TestContact, self).tearDown()

    def test_01_send_contact_form_success(self):
        form = ContactUs()
        form.email.data = "test@example.com"
        form.message.data = "Message 1"
        send_contact_form(form)

    def test_02_send_contact_form_spam(self):
        form = ContactUs()
        form.email.data = "test@example.com"
        form.subject.data = "My suspicious message"
        form.message.data = "Message 2"
        send_contact_form(form)
