from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from portality.events.consumers.journal_assed_assigned_notify import JournalAssedAssignedNotify
from doajtest.fixtures import JournalFixtureFactory
import time


class TestJournalAssedAssignedNotify(DoajTestCase):
    def setUp(self):
        super(TestJournalAssedAssignedNotify, self).setUp()

    def tearDown(self):
        super(TestJournalAssedAssignedNotify, self).tearDown()

    def test_consumes(self):
        event = models.Event(constants.EVENT_JOURNAL_ASSED_ASSIGNED, context={"journal" : {}})
        assert JournalAssedAssignedNotify.consumes(event)

        event = models.Event("test:event", context={"journal" : {}})
        assert not JournalAssedAssignedNotify.consumes(event)

        event = models.Event(constants.EVENT_JOURNAL_ASSED_ASSIGNED)
        assert not JournalAssedAssignedNotify.consumes(event)

    def test_consume_success(self):
        self._make_and_push_test_context("/")

        source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        app = models.Journal(**source)
        # app.save()

        acc = models.Account()
        acc.set_id(app.editor)
        acc.set_email("test@example.com")
        acc.save(blocking=True)

        event = models.Event(constants.EVENT_JOURNAL_ASSED_ASSIGNED, context={"journal" : app.data})
        JournalAssedAssignedNotify.consume(event)

        time.sleep(2)
        ns = models.Notification.all()
        assert len(ns) == 1

        n = ns[0]
        assert n.who == app.editor
        assert n.created_by == JournalAssedAssignedNotify.ID
        assert n.classification == constants.NOTIFICATION_CLASSIFICATION_ASSIGN
        assert n.long is not None
        assert n.short is not None
        assert n.action is not None
        assert not n.is_seen()

    def test_consume_fail(self):
        event = models.Event(constants.EVENT_JOURNAL_ASSED_ASSIGNED, context={"journal": {"key" : "value"}})
        with self.assertRaises(exceptions.NoSuchObjectException):
            JournalAssedAssignedNotify.consume(event)

        source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        del source["admin"]["editor"]
        app = models.Journal(**source)
        # app.save(blocking=True)

        event = models.Event(constants.EVENT_JOURNAL_ASSED_ASSIGNED, context={"journal": app.data})
        with self.assertRaises(exceptions.NoSuchPropertyException):
            JournalAssedAssignedNotify.consume(event)
