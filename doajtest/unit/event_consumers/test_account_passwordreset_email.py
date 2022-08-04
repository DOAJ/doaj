from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from portality.events.consumers.account_passwordreset_email import AccountPasswordResetEmail
from doajtest.fixtures import AccountFixtureFactory
import uuid
from io import StringIO
import logging
import re

# A regex string for searching the log entries
email_log_regex = 'template.*%s.*to:\[u{0,1}\'%s.*subject:.*%s'

# A string present in each email log entry (for counting them)
email_count_string = 'Email template'


class TestAccountPasswordResetEmail(DoajTestCase):
    def setUp(self):
        super(TestAccountPasswordResetEmail, self).setUp()
        self.info_stream = StringIO()
        self.read_info = logging.StreamHandler(self.info_stream)
        self.read_info.setLevel(logging.INFO)
        self.app_test.logger.addHandler(self.read_info)

    def tearDown(self):
        super(TestAccountPasswordResetEmail, self).tearDown()

        # Blank the info_stream and remove the error handler from the app
        self.info_stream.truncate(0)
        self.app_test.logger.removeHandler(self.read_info)

    def test_consumes(self):
        source = AccountFixtureFactory.make_publisher_source()
        acc = models.Account(**source)
        acc.clear_password()
        reset_token = uuid.uuid4().hex
        acc.set_reset_token(reset_token, 86400)

        event = models.Event(constants.EVENT_ACCOUNT_PASSWORD_RESET, context={"account" : acc.data})
        assert AccountPasswordResetEmail.consumes(event)

        event = models.Event(constants.EVENT_ACCOUNT_PASSWORD_RESET)
        assert not AccountPasswordResetEmail.consumes(event)

        event = models.Event("test:event", context={"application" : "2345"})
        assert not AccountPasswordResetEmail.consumes(event)

    def test_consume_success(self):
        self._make_and_push_test_context("/")

        source = AccountFixtureFactory.make_publisher_source()
        acc = models.Account(**source)
        acc.clear_password()
        reset_token = uuid.uuid4().hex
        acc.set_reset_token(reset_token, 86400)

        event = models.Event(constants.EVENT_ACCOUNT_PASSWORD_RESET, context={"account": acc.data})

        AccountPasswordResetEmail.consume(event)

        # Use the captured info stream to get email send logs
        info_stream_contents = self.info_stream.getvalue()

        # We expect one email sent:
        #   * to the applicant, informing them the application was received
        template = re.escape('account_password_reset.jinja2')
        to = re.escape(acc.email)
        subject = "Directory of Open Access Journals - password reset"
        email_matched = re.search(email_log_regex % (template, to, subject),
                                         info_stream_contents,
                                         re.DOTALL)
        assert bool(email_matched)
        assert len(re.findall(email_count_string, info_stream_contents)) == 1

    def test_consume_fail(self):
        source = AccountFixtureFactory.make_publisher_source()
        acc = models.Account(**source)
        # we don't set the reset token

        event = models.Event(constants.EVENT_ACCOUNT_PASSWORD_RESET, context={"account": acc.data})
        with self.assertRaises(exceptions.NoSuchPropertyException):
            AccountPasswordResetEmail.consume(event)

