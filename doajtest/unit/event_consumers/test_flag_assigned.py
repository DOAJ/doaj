from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from portality.events.consumers.flag_assigned import FlagAssigned
from doajtest.fixtures import JournalFixtureFactory
import time


class TestFlagAssigned(DoajTestCase):
    def setUp(self):
        super(TestFlagAssigned, self).setUp()

    def tearDown(self):
        super(TestFlagAssigned, self).tearDown()

    def test_should_consume(self):
        event = models.Event(constants.EVENT_FLAG_ASSIGNED, context={"assignee": "rudolph", "journal": JournalFixtureFactory.make_journal_source()})
        assert FlagAssigned.should_consume(event)

    def test_consume_success(self):
        with self._make_and_push_test_context_manager("/"):

            jsource = JournalFixtureFactory.make_journal_source()
            j = models.Journal(**jsource)
            j.save()

            acc = models.Account()
            acc.set_id("LadyBranbury")
            acc.set_email("ladybranbury@example.com")
            acc.save()

            event = models.Event(constants.EVENT_FLAG_ASSIGNED, context={"journal": j.data, "assignee": acc.id})
            FlagAssigned.consume(event)

            time.sleep(1)
            ns = models.Notification.all()
            assert len(ns) == 1

            n = ns[0]
            assert n.who == "LadyBranbury"
            assert n.created_by == FlagAssigned.ID
            assert n.classification == constants.NOTIFICATION_CLASSIFICATION_ASSIGN
            assert n.long is not None
            assert n.short is not None
            assert n.action is not None
            assert not n.is_seen()

    def test_consume_fail(self):
        event = models.Event(constants.EVENT_FLAG_ASSIGNED, context={"application": {'stuff': 'nonsense'}})
        with self.assertRaises(exceptions.NoSuchObjectException):
            FlagAssigned.consume(event)

