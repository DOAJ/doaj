from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from portality.events.consumers.application_editor_group_assigned_notify import ApplicationEditorGroupAssignedNotify
from doajtest.fixtures import ApplicationFixtureFactory
import time


class TestApplicationEditorGroupAssignedNotify(DoajTestCase):
    def setUp(self):
        super(TestApplicationEditorGroupAssignedNotify, self).setUp()

    def tearDown(self):
        super(TestApplicationEditorGroupAssignedNotify, self).tearDown()

    def test_consumes(self):
        event = models.Event(constants.EVENT_APPLICATION_EDITOR_GROUP_ASSIGNED, context={"application" : {}})
        assert ApplicationEditorGroupAssignedNotify.consumes(event)

        event = models.Event("test:event", context={"application" : {}})
        assert not ApplicationEditorGroupAssignedNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_EDITOR_GROUP_ASSIGNED)
        assert not ApplicationEditorGroupAssignedNotify.consumes(event)

    def test_consume_success(self):
        self._make_and_push_test_context("/")

        source = ApplicationFixtureFactory.make_application_source()
        app = models.Application(**source)
        # app.save()

        acc = models.Account()
        acc.set_id("editor")
        acc.set_email("test@example.com")
        acc.save()

        eg = models.EditorGroup()
        eg.set_name(app.editor_group)
        eg.set_editor("editor")
        eg.save(blocking=True)

        event = models.Event(constants.EVENT_APPLICATION_EDITOR_GROUP_ASSIGNED, context={"application" : app.data})
        ApplicationEditorGroupAssignedNotify.consume(event)

        time.sleep(2)
        ns = models.Notification.all()
        assert len(ns) == 1

        n = ns[0]
        assert n.who == "editor"
        assert n.created_by == ApplicationEditorGroupAssignedNotify.ID
        assert n.classification == constants.NOTIFICATION_CLASSIFICATION_ASSIGN
        assert n.message is not None
        assert n.action is not None
        assert not n.is_seen()

    def test_consume_fail(self):
        event = models.Event(constants.EVENT_APPLICATION_EDITOR_GROUP_ASSIGNED, context={"application": {"key" : "value"}})
        with self.assertRaises(exceptions.NoSuchObjectException):
            ApplicationEditorGroupAssignedNotify.consume(event)

        source = ApplicationFixtureFactory.make_application_source()
        app = models.Application(**source)
        # app.save(blocking=True)

        eg = models.EditorGroup()
        eg.set_name(app.editor_group)
        eg.save(blocking=True)

        event = models.Event(constants.EVENT_APPLICATION_EDITOR_GROUP_ASSIGNED, context={"application": app.data})
        with self.assertRaises(exceptions.NoSuchPropertyException):
            ApplicationEditorGroupAssignedNotify.consume(event)
