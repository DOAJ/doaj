from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from portality.events.consumers.application_editor_completed_notify import ApplicationEditorCompletedNotify
from doajtest.fixtures import ApplicationFixtureFactory
import time


class TestApplicationEditorCompletedNotify(DoajTestCase):
    def setUp(self):
        super(TestApplicationEditorCompletedNotify, self).setUp()

    def tearDown(self):
        super(TestApplicationEditorCompletedNotify, self).tearDown()

    def test_consumes(self):
        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application": ApplicationFixtureFactory.make_application_source(), "old_status": "in progress", "new_status": "completed"})
        assert ApplicationEditorCompletedNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_STATUS,
                             context={"application": ApplicationFixtureFactory.make_application_source(), "old_status": "completed", "new_status": "completed"})
        assert not ApplicationEditorCompletedNotify.consumes(event)

        event = models.Event("test:event", context={"application": ApplicationFixtureFactory.make_application_source()})
        assert not ApplicationEditorCompletedNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_STATUS)
        assert not ApplicationEditorCompletedNotify.consumes(event)

    def test_consume_success(self):
        self._make_and_push_test_context("/")

        source = ApplicationFixtureFactory.make_application_source()
        app = models.Application(**source)
        app.save()

        acc = models.Account()
        acc.set_id("ed")
        acc.set_email("test@example.com")
        acc.save()

        eg = models.EditorGroup()
        eg.set_name(app.editor_group)
        eg.set_editor(acc.id)
        eg.save(blocking=True)

        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application": app, "old_status": "in progress", "new_status": "completed"})
        ApplicationEditorCompletedNotify.consume(event)

        time.sleep(1)
        ns = models.Notification.all()
        assert len(ns) == 1

        n = ns[0]
        assert n.who == "ed"
        assert n.created_by == ApplicationEditorCompletedNotify.ID
        assert n.classification == constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
        assert n.message is not None
        assert n.action is not None
        assert not n.is_seen()

    def test_consume_fail(self):
        event = models.Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED, context={"application": {'stuff': 'nonsense'}})
        with self.assertRaises(exceptions.NoSuchObjectException):
            ApplicationEditorCompletedNotify.consume(event)

