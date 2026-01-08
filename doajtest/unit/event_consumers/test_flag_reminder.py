from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from portality.events.consumers.flag_reminder import FlagReminder
from doajtest.fixtures import JournalFixtureFactory
import time


class TestFlagReminder(DoajTestCase):
    def setUp(self):
        super(TestFlagReminder, self).setUp()

    def tearDown(self):
        super(TestFlagReminder, self).tearDown()

    def test_should_consume(self):
        event = models.Event(constants.EVENT_FLAG_REMINDER, context={"assignee": "rudolph", "journal": JournalFixtureFactory.make_journal_source()})
        assert FlagReminder.should_consume(event)

    def test_consume_success(self):
        with self._make_and_push_test_context_manager("/"):

            jsource = JournalFixtureFactory.make_journal_source()
            j = models.Journal(**jsource)
            j.save()

            acc = models.Account()
            acc.set_id("SirLancelittle")
            acc.set_email("lancelittle@example.com")
            acc.save()

            event = models.Event(constants.EVENT_FLAG_REMINDER, context={"journal": j.data, "assignee": acc.id})
            FlagReminder.consume(event)

            time.sleep(1)
            ns = models.Notification.all()
            assert len(ns) == 1

            n = ns[0]
            assert n.who == "SirLancelittle"
            assert n.created_by == FlagReminder.ID
            assert n.classification == constants.NOTIFICATION_CLASSIFICATION_STATUS
            assert n.long is not None
            assert n.short is not None
            assert n.action is not None
            assert not n.is_seen()

    def test_consume_fail(self):
        event = models.Event(constants.EVENT_FLAG_REMINDER, context={"application": {'stuff': 'nonsense'}})
        with self.assertRaises(exceptions.NoSuchObjectException):
            FlagReminder.consume(event)

