from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from portality.events.consumers.application_maned_ready_notify import ApplicationManedReadyNotify
from doajtest.fixtures import ApplicationFixtureFactory
import time


class TestApplicationManedReadyNotify(DoajTestCase):
    def setUp(self):
        super(TestApplicationManedReadyNotify, self).setUp()

    def tearDown(self):
        super(TestApplicationManedReadyNotify, self).tearDown()

    def test_consumes(self):
        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application" : {}, "old_status" : "in progress", "new_status": "ready"})
        assert ApplicationManedReadyNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_STATUS,
                             context={"application": {}, "old_status": "ready", "new_status": "ready"})
        assert not ApplicationManedReadyNotify.consumes(event)

        event = models.Event("test:event", context={"application" : "2345"})
        assert not ApplicationManedReadyNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_STATUS)
        assert not ApplicationManedReadyNotify.consumes(event)

    def test_consume_success(self):
        self._make_and_push_test_context("/")

        source = ApplicationFixtureFactory.make_application_source()
        app = models.Application(**source)
        # app.save()

        acc = models.Account()
        acc.set_id("maned")
        acc.set_email("test@example.com")
        acc.save()

        eg = models.EditorGroup()
        eg.set_name(app.editor_group)
        eg.set_maned(acc.id)
        eg.save(blocking=True)

        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application" : app.data, "old_status": "in progress", "new_status": "ready"})
        ApplicationManedReadyNotify.consume(event)

        time.sleep(2)
        ns = models.Notification.all()
        assert len(ns) == 1

        n = ns[0]
        assert n.who == "maned"
        assert n.created_by == ApplicationManedReadyNotify.ID
        assert n.classification == constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
        assert n.message is not None
        assert n.action is not None
        assert not n.is_seen()

    def test_consume_fail(self):
        event = models.Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED, context={"application": {"key" : "value"}})
        with self.assertRaises(exceptions.NoSuchObjectException):
            ApplicationManedReadyNotify.consume(event)

