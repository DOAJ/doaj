from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from portality.events.consumers.journal_editor_group_assigned_notify import JournalEditorGroupAssignedNotify
from doajtest.fixtures import JournalFixtureFactory
import time


class TestJournalEditorGroupAssignedNotify(DoajTestCase):
    def setUp(self):
        super(TestJournalEditorGroupAssignedNotify, self).setUp()

    def tearDown(self):
        super(TestJournalEditorGroupAssignedNotify, self).tearDown()

    def test_consumes(self):
        event = models.Event(constants.EVENT_JOURNAL_EDITOR_GROUP_ASSIGNED, context={"journal" : {}})
        assert JournalEditorGroupAssignedNotify.consumes(event)

        event = models.Event("test:event", context={"journal" : {}})
        assert not JournalEditorGroupAssignedNotify.consumes(event)

        event = models.Event(constants.EVENT_JOURNAL_EDITOR_GROUP_ASSIGNED)
        assert not JournalEditorGroupAssignedNotify.consumes(event)

    def test_consume_success(self):
        self._make_and_push_test_context("/")

        source = JournalFixtureFactory.make_journal_source(True)
        app = models.Journal(**source)
        # app.save()

        acc = models.Account()
        acc.set_id("editor")
        acc.set_email("test@example.com")
        acc.save()

        eg = models.EditorGroup()
        eg.set_name(app.editor_group)
        eg.set_editor("editor")
        eg.save(blocking=True)

        event = models.Event(constants.EVENT_JOURNAL_EDITOR_GROUP_ASSIGNED, context={"journal" : app.data})
        JournalEditorGroupAssignedNotify.consume(event)

        time.sleep(2)
        ns = models.Notification.all()
        assert len(ns) == 1

        n = ns[0]
        assert n.who == "editor"
        assert n.created_by == JournalEditorGroupAssignedNotify.ID
        assert n.classification == constants.NOTIFICATION_CLASSIFICATION_ASSIGN
        assert n.message is not None
        assert n.action is not None
        assert not n.is_seen()

    def test_consume_fail(self):
        event = models.Event(constants.EVENT_JOURNAL_EDITOR_GROUP_ASSIGNED, context={"journal": {"key" : "value"}})
        with self.assertRaises(exceptions.NoSuchObjectException):
            JournalEditorGroupAssignedNotify.consume(event)

        source = JournalFixtureFactory.make_journal_source(True)
        app = models.Journal(**source)
        # app.save(blocking=True)

        eg = models.EditorGroup()
        eg.set_name(app.editor_group)
        eg.save(blocking=True)

        event = models.Event(constants.EVENT_JOURNAL_EDITOR_GROUP_ASSIGNED, context={"journal": app.data})
        with self.assertRaises(exceptions.NoSuchPropertyException):
            JournalEditorGroupAssignedNotify.consume(event)
