from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from portality.events.consumers.application_assed_inprogress_notify import ApplicationAssedInprogressNotify
from doajtest.fixtures import ApplicationFixtureFactory
import time


class TestApplicationAssedInprogressNotify(DoajTestCase):
    def setUp(self):
        super(TestApplicationAssedInprogressNotify, self).setUp()

    def tearDown(self):
        super(TestApplicationAssedInprogressNotify, self).tearDown()

    def test_consumes(self):

        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application" : {}, "old_status" : "completed", "new_status": "in progress"})
        assert ApplicationAssedInprogressNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_STATUS,
                             context={"old_status": "ready", "new_status": "ready"})
        assert not ApplicationAssedInprogressNotify.consumes(event)

        event = models.Event("test:event", context={"application" : "2345"})
        assert not ApplicationAssedInprogressNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_STATUS)
        assert not ApplicationAssedInprogressNotify.consumes(event)

    def test_consume_success(self):
        self._make_and_push_test_context("/")

        source = ApplicationFixtureFactory.make_application_source()
        app = models.Application(**source)
        # app.save()

        acc = models.Account()
        acc.set_id("associate")
        acc.set_email("test@example.com")
        acc.save()

        eg = models.EditorGroup()
        eg.set_name(app.editor_group)
        eg.set_maned(acc.id)
        eg.save(blocking=True)

        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application" : app.data, "old_status": "completed", "new_status": "in progress"})
        ApplicationAssedInprogressNotify.consume(event)

        time.sleep(2)
        ns = models.Notification.all()
        assert len(ns) == 1

        n = ns[0]
        assert n.who == "associate"
        assert n.created_by == ApplicationAssedInprogressNotify.ID
        assert n.classification == constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
        assert n.message is not None
        assert n.action is not None
        assert not n.is_seen()

    def test_consume_fail(self):
        event = models.Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED, context={"application": {"key" : "value"}})
        with self.assertRaises(exceptions.NoSuchObjectException):
            ApplicationAssedInprogressNotify.consume(event)

