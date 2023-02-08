from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from doajtest.fixtures import JournalFixtureFactory
from portality.events.consumers.journal_discontinuing_soon_notify import JournalDiscontinuingSoonNotify
from doajtest.fixtures import BackgroundFixtureFactory
import time


class TestJournalDiscontinuingSoonNotify(DoajTestCase):
    def setUp(self):
        super(TestJournalDiscontinuingSoonNotify, self).setUp()

    def tearDown(self):
        super(TestJournalDiscontinuingSoonNotify, self).tearDown()

    def test_consumes(self):
        event = models.Event(constants.EVENT_JOURNAL_DISCONTINUING_SOON, context={"job" : {}})
        assert not JournalDiscontinuingSoonNotify.consumes(event)

        event = models.Event("test:event", context={"data" : {"1234"}})
        assert not JournalDiscontinuingSoonNotify.consumes(event)

        event = models.Event("test:event", context={"data": {}})
        assert not JournalDiscontinuingSoonNotify.consumes(event)

        event = models.Event(constants.EVENT_JOURNAL_DISCONTINUING_SOON)
        assert not JournalDiscontinuingSoonNotify.consumes(event)

        event = models.Event(constants.EVENT_JOURNAL_DISCONTINUING_SOON, context = {"data": {"1234"}, "job": {"1234"}})
        assert JournalDiscontinuingSoonNotify.consumes(event)

    def test_consume_success(self):
        self._make_and_push_test_context("/")

        source = BackgroundFixtureFactory.example()
        bj = models.BackgroundJob(**source)
        # bj.save(blocking=True)

        acc = models.Account()
        acc.set_id('testuser')
        acc.set_email("test@example.com")
        acc.add_role('admin')
        acc.save(blocking=True)



        event = models.Event(constants.BACKGROUND_JOB_FINISHED, context={"job" : bj.data, "data" : JournalFixtureFactory.make_many_journal_sources(2)})
        JournalDiscontinuingSoonNotify.consume(event)

        time.sleep(2)
        ns = models.Notification.all()
        assert len(ns) == 1

        n = ns[0]
        assert n.who == acc.id
        assert n.created_by == JournalDiscontinuingSoonNotify.ID
        assert n.classification == constants.NOTIFICATION_CLASSIFICATION_STATUS
        assert n.long is not None
        assert n.short is not None
        assert n.action is not None
        assert not n.is_seen()

    def test_consume_fail(self):
        event = models.Event(constants.NOTIFICATION_CLASSIFICATION_STATUS, context={"job": "abcd"})
        with self.assertRaises(exceptions.NoSuchObjectException):
            JournalDiscontinuingSoonNotify.consume(event)
