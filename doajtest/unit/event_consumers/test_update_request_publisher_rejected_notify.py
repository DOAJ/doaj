from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from portality.events.consumers.update_request_publisher_rejected_notify import UpdateRequestPublisherRejectedNotify
from doajtest.fixtures import ApplicationFixtureFactory
import time


class TestUpdateRequestPublisherRejectedNotify(DoajTestCase):
    def setUp(self):
        super(TestUpdateRequestPublisherRejectedNotify, self).setUp()

    def tearDown(self):
        super(TestUpdateRequestPublisherRejectedNotify, self).tearDown()

    def test_consumes(self):
        source = ApplicationFixtureFactory.make_application_source()

        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application" : source, "old_status" : "in progress", "new_status": "rejected"})
        assert UpdateRequestPublisherRejectedNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_STATUS,
                             context={"old_status": "rejected", "new_status": "rejected"})
        assert not UpdateRequestPublisherRejectedNotify.consumes(event)

        event = models.Event("test:event", context={"application" : "2345"})
        assert not UpdateRequestPublisherRejectedNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_STATUS)
        assert not UpdateRequestPublisherRejectedNotify.consumes(event)

    def test_consume_success(self):
        self._make_and_push_test_context("/")

        acc = models.Account()
        acc.set_id("publisher")
        acc.set_email("test@example.com")
        acc.save(blocking=True)

        source = ApplicationFixtureFactory.make_application_source()

        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application" : source, "old_status": "in progress", "new_status": "rejected"})
        UpdateRequestPublisherRejectedNotify.consume(event)

        time.sleep(2)
        ns = models.Notification.all()
        assert len(ns) == 1

        n = ns[0]
        assert n.who == "publisher"
        assert n.created_by == UpdateRequestPublisherRejectedNotify.ID
        assert n.classification == constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
        assert n.long is not None
        assert n.short is not None
        assert not n.is_seen()

    def test_consume_fail(self):
        # application model error
        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application": {"key" : "value"}})
        with self.assertRaises(exceptions.NoSuchObjectException):
            UpdateRequestPublisherRejectedNotify.consume(event)

        # no owner
        source = ApplicationFixtureFactory.make_application_source()
        del source["admin"]["owner"]

        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={
            "application": source,
            "old_status": "in progress",
            "new_status": "rejected"
        })
        UpdateRequestPublisherRejectedNotify.consume(event)
        time.sleep(2)
        ns = models.Notification.all()
        assert len(ns) == 0

