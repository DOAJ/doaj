from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from portality.events.consumers.update_request_maned_editor_group_assigned_notify import UpdateRequestManedEditorGroupAssignedNotify
from doajtest.fixtures import ApplicationFixtureFactory
import time


class TestUpdateRequestManedEditorGroupAssignedNotify(DoajTestCase):
    def setUp(self):
        super(TestUpdateRequestManedEditorGroupAssignedNotify, self).setUp()

    def tearDown(self):
        super(TestUpdateRequestManedEditorGroupAssignedNotify, self).tearDown()

    def test_should_consume(self):
        event = models.Event(constants.EVENT_APPLICATION_EDITOR_GROUP_ASSIGNED, context={"application" : {}})
        assert UpdateRequestManedEditorGroupAssignedNotify.should_consume(event)

        event = models.Event("test:event", context={"application" : {}})
        assert not UpdateRequestManedEditorGroupAssignedNotify.should_consume(event)

        event = models.Event(constants.EVENT_APPLICATION_EDITOR_GROUP_ASSIGNED)
        assert not UpdateRequestManedEditorGroupAssignedNotify.should_consume(event)

    def test_consume_success(self):
        with self._make_and_push_test_context_manager("/"):

            source = ApplicationFixtureFactory.make_application_source()
            app = models.Application(**source)
            app.application_type = constants.APPLICATION_TYPE_UPDATE_REQUEST

            acc = models.Account()
            acc.set_id("maned")
            acc.set_email("test@example.com")
            acc.save()

            eg = models.EditorGroup()
            eg.set_name(app.editor_group)
            eg.set_maned("maned")
            eg.save(blocking=True)

            event = models.Event(constants.EVENT_APPLICATION_EDITOR_GROUP_ASSIGNED, context={"application" : app.data})
            UpdateRequestManedEditorGroupAssignedNotify.consume(event)

            time.sleep(1)
            ns = models.Notification.all()
            assert len(ns) == 1

            n = ns[0]
            assert n.who == "maned"
            assert n.created_by == UpdateRequestManedEditorGroupAssignedNotify.ID
            assert n.classification == constants.NOTIFICATION_CLASSIFICATION_ASSIGN
            assert n.long is not None
            assert n.short is not None
            assert n.action is not None
            assert not n.is_seen()

    def test_consume_fail(self):
        event = models.Event(constants.EVENT_APPLICATION_EDITOR_GROUP_ASSIGNED, context={"application": {"key" : "value"}})
        with self.assertRaises(exceptions.NoSuchObjectException):
            UpdateRequestManedEditorGroupAssignedNotify.consume(event)

        source = ApplicationFixtureFactory.make_application_source()
        app = models.Application(**source)
        app.application_type = constants.APPLICATION_TYPE_NEW_APPLICATION
        # app.save(blocking=True)

        eg = models.EditorGroup()
        eg.set_name(app.editor_group)
        eg.save(blocking=True)

        event = models.Event(constants.EVENT_APPLICATION_EDITOR_GROUP_ASSIGNED, context={"application": app.data})
        UpdateRequestManedEditorGroupAssignedNotify.consume(event)

        time.sleep(1)
        ns = models.Notification.all()
        assert len(ns) == 0