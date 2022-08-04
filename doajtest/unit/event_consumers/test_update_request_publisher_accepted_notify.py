from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from portality.events.consumers.update_request_publisher_accepted_notify import UpdateRequestPublisherAcceptedNotify
from doajtest.fixtures import ApplicationFixtureFactory
import time


class TestUpdateRequestPublisherAcceptedNotify(DoajTestCase):
    def setUp(self):
        super(TestUpdateRequestPublisherAcceptedNotify, self).setUp()

    def tearDown(self):
        super(TestUpdateRequestPublisherAcceptedNotify, self).tearDown()

    def test_consumes(self):
        source = ApplicationFixtureFactory.make_application_source()

        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application" : source, "old_status" : "in progress", "new_status": "accepted"})
        assert UpdateRequestPublisherAcceptedNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_STATUS,
                             context={"application": source, "old_status": "ready", "new_status": "ready"})
        assert not UpdateRequestPublisherAcceptedNotify.consumes(event)

        event = models.Event("test:event", context={"application" : source})
        assert not UpdateRequestPublisherAcceptedNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_STATUS)
        assert not UpdateRequestPublisherAcceptedNotify.consumes(event)

    def test_consume_success(self):
        self._make_and_push_test_context("/")

        source = ApplicationFixtureFactory.make_application_source()
        app = models.Application(**source)
        # app.save()

        acc = models.Account()
        acc.set_id("publisher")
        acc.set_email("test@example.com")
        acc.save(blocking=True)

        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application" : app.data, "old_status": "in progress", "new_status": "accepted"})
        UpdateRequestPublisherAcceptedNotify.consume(event)

        time.sleep(2)
        ns = models.Notification.all()
        assert len(ns) == 1

        n = ns[0]
        assert n.who == "publisher"
        assert n.created_by == UpdateRequestPublisherAcceptedNotify.ID
        assert n.classification == constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
        assert n.long is not None
        assert n.short is not None
        assert n.action is not None
        assert not n.is_seen()

    def test_consume_fail(self):
        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application": {"key" : "value"}})
        with self.assertRaises(exceptions.NoSuchObjectException):
            UpdateRequestPublisherAcceptedNotify.consume(event)

