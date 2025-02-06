from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from portality.events.consumers.account_created_email import AccountCreatedEmail
from doajtest.fixtures import AccountFixtureFactory
import uuid
from io import StringIO
import logging
import re
from portality.ui import templates

# A regex string for searching the log entries
email_log_regex = 'template.*%s.*to:\[u{0,1}\'%s.*subject:.*%s'

# A string present in each email log entry (for counting them)
email_count_string = 'Email template'


class TestAccountCreatedEmail(DoajTestCase):
    def setUp(self):
        super(TestAccountCreatedEmail, self).setUp()
        self.info_stream = StringIO()
        self.read_info = logging.StreamHandler(self.info_stream)
        self.read_info.setLevel(logging.INFO)
        self.app_test.logger.addHandler(self.read_info)

    def tearDown(self):
        super(TestAccountCreatedEmail, self).tearDown()

        # Blank the info_stream and remove the error handler from the app
        self.info_stream.truncate(0)
        self.app_test.logger.removeHandler(self.read_info)

    def test_should_consume(self):
        source = AccountFixtureFactory.make_publisher_source()
        acc = models.Account(**source)
        acc.clear_password()
        reset_token = uuid.uuid4().hex
        acc.set_reset_token(reset_token, 86400)

        event = models.Event(constants.EVENT_ACCOUNT_CREATED, context={"account" : acc.data})
        assert AccountCreatedEmail.should_consume(event)

        event = models.Event(constants.EVENT_ACCOUNT_CREATED)
        assert not AccountCreatedEmail.should_consume(event)

        event = models.Event("test:event", context={"application" : "2345"})
        assert not AccountCreatedEmail.should_consume(event)

    def test_consume_success(self):
        with self._make_and_push_test_context_manager("/"):

            source = AccountFixtureFactory.make_publisher_source()
            acc = models.Account(**source)
            acc.clear_password()
            reset_token = uuid.uuid4().hex
            acc.set_reset_token(reset_token, 86400)

            event = models.Event(constants.EVENT_ACCOUNT_CREATED, context={"account": acc.data})

            AccountCreatedEmail.consume(event)

            # Use the captured info stream to get email send logs
            info_stream_contents = self.info_stream.getvalue()

        # We expect one email sent:
        #   * to the applicant, informing them the application was received
        template = re.escape(templates.EMAIL_ACCOUNT_CREATED)
        to = re.escape(acc.email)
        subject = "Directory of Open Access Journals - account created, please verify your email address"
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
            AccountCreatedEmail.consume(event)

