from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from portality.events.consumers.application_publisher_quickreject_notify import ApplicationPublisherQuickRejectNotify
from doajtest.fixtures import ApplicationFixtureFactory
import time


class TestApplicationPublisherQuickRejectNotify(DoajTestCase):
    def setUp(self):
        super(TestApplicationPublisherQuickRejectNotify, self).setUp()

    def tearDown(self):
        super(TestApplicationPublisherQuickRejectNotify, self).tearDown()

    def test_consumes(self):

        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application" : {}, "old_status" : "in progress", "new_status": "rejected", "process": constants.PROCESS__QUICK_REJECT})
        assert ApplicationPublisherQuickRejectNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_STATUS,
                             context={"application": {}, "old_status": "in progress", "new_status": "rejected"})
        assert not ApplicationPublisherQuickRejectNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_STATUS,
                             context={"old_status": "rejected", "new_status": "rejected"})
        assert not ApplicationPublisherQuickRejectNotify.consumes(event)

        event = models.Event("test:event", context={"application" : {}, "old_status" : "in progress", "new_status": "rejected", "process": constants.PROCESS__QUICK_REJECT})
        assert not ApplicationPublisherQuickRejectNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_STATUS)
        assert not ApplicationPublisherQuickRejectNotify.consumes(event)

    def test_consume_success(self):
        self._make_and_push_test_context("/")

        acc = models.Account()
        acc.set_id("publisher")
        acc.set_email("test@example.com")
        acc.save(blocking=True)

        source = ApplicationFixtureFactory.make_application_source()

        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={
            "application" : source,
            "old_status": "in progress",
            "new_status": "rejected",
            "process": constants.PROCESS__QUICK_REJECT,
            "note": "my note"
        })
        ApplicationPublisherQuickRejectNotify.consume(event)

        time.sleep(2)
        ns = models.Notification.all()
        assert len(ns) == 1

        n = ns[0]
        assert n.who == "publisher"
        assert n.created_by == ApplicationPublisherQuickRejectNotify.ID
        assert n.classification == constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
        assert "my note" in n.long
        assert n.short is not None
        assert not n.is_seen()

    def test_consume_fail(self):
        # invalid application model
        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application": {"key" : "value"}})
        with self.assertRaises(exceptions.NoSuchObjectException):
            ApplicationPublisherQuickRejectNotify.consume(event)

        # no owner
        source = ApplicationFixtureFactory.make_application_source()
        del source["admin"]["owner"]

        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={
            "application": source,
            "old_status": "in progress",
            "new_status": "rejected",
            "process": constants.PROCESS__QUICK_REJECT,
            "note": "my note"
        })
        ApplicationPublisherQuickRejectNotify.consume(event)
        time.sleep(2)
        ns = models.Notification.all()
        assert len(ns) == 0
