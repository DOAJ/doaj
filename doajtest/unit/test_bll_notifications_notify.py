import re
import logging
from io import StringIO
from doajtest.helpers import DoajTestCase
from portality import models
from portality.bll import DOAJ
from portality.ui.messages import Messages
from portality.ui import templates
from portality.bll.exceptions import NoSuchObjectException, NoSuchPropertyException

# A regex string for searching the log entries
EMAIL_LOG_REGEX = 'template.*%s.*to:\[u{0,1}\'%s.*subject:.*%s'


class TestBLLNotifications(DoajTestCase):

    def setUp(self):
        super(TestBLLNotifications, self).setUp()

        # Register a new log handler so we can inspect the info logs
        self.info_stream = StringIO()
        self.read_info = logging.StreamHandler(self.info_stream)
        self.read_info.setLevel(logging.INFO)
        self.app_test.logger.addHandler(self.read_info)

    def tearDown(self):
        super(TestBLLNotifications, self).tearDown()

        # Blank the info_stream and remove the error handler from the app
        self.info_stream.truncate(0)
        self.app_test.logger.removeHandler(self.read_info)

    def test_01_notify(self):
        acc = models.Account()
        acc.set_id("testuser")
        acc.set_email("test@example.com")
        acc.save(blocking=True)

        n = models.Notification()
        n.who = "testuser"
        n.long = "my message"
        n.short = "short note"
        n.action = "/test"
        n.classification = "test_class"
        n.created_by = "test:notify"

        svc = DOAJ.notificationsService()
        n = svc.notify(n)

        assert n.id is not None
        n2 = models.Notification.pull(n.id)
        assert n2.who == "testuser"
        assert n2.long == "my message"
        assert n2.short == "short note"
        assert n2.action == "/test"
        assert n2.classification == "test_class"
        assert n2.created_by == "test:notify"
        assert not n2.is_seen()

        # Use the captured info stream to get email send logs
        info_stream_contents = self.info_stream.getvalue()

        # check an email is sent
        template = re.escape(templates.EMAIL_NOTIFICATION)
        to = re.escape('test@example.com')
        subject = n2.short
        email_matched = re.search(
            EMAIL_LOG_REGEX % (template, to, subject),
            info_stream_contents,
            re.DOTALL)
        assert bool(email_matched)

    def test_02_notify_errors(self):
        n = models.Notification()
        n.who = "testuser"
        n.long = "my message"
        n.short = "short note"
        n.action = "/test"
        n.classification = "test_class"
        n.created_by = "test:notify"

        svc = DOAJ.notificationsService()

        with self.assertRaises(NoSuchObjectException):
            n = svc.notify(n)

        acc = models.Account()
        acc.set_id("testuser")
        acc.save(blocking=True)

        with self.assertRaises(NoSuchPropertyException):
            n = svc.notify(n)
