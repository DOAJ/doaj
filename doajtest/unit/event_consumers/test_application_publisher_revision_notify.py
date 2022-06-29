from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from doajtest.fixtures import ApplicationFixtureFactory
import time

from portality.events.consumers.application_publisher_revision_notify import ApplicationPublisherRevisionNotify


class TestApplicationPublisherRevisionNotify(DoajTestCase):
    def setUp(self):
        super(TestApplicationPublisherRevisionNotify, self).setUp()

    def tearDown(self):
        super(TestApplicationPublisherRevisionNotify, self).tearDown()

    def test_consumes(self):
        source = ApplicationFixtureFactory.make_application_source()

        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application": {}, "old_status": "in progress", "new_status": "revisions_required"})
        assert ApplicationPublisherRevisionNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_STATUS,
                             context={"application": {}, "old_status": "revisions_required", "new_status": "revisions_required"})
        assert not ApplicationPublisherRevisionNotify.consumes(event)

        event = models.Event("test:event", context={"application" : {}})
        assert not ApplicationPublisherRevisionNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_STATUS)
        assert not ApplicationPublisherRevisionNotify.consumes(event)

    def test_consume_success(self):
        self._make_and_push_test_context("/")

        acc = models.Account()
        acc.set_id("publisher")
        acc.set_email("test@example.com")
        acc.save()

        source = ApplicationFixtureFactory.make_application_source()
        event = models.Event(constants.EVENT_APPLICATION_STATUS,
                             context={"application": source, "old_status": "in progress",
                                      "new_status": "revisions_required"})

        # event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application": "abcdefghijk", "old_status": "in progress", "new_status": "revisions_required"})
        ApplicationPublisherRevisionNotify.consume(event)

        time.sleep(2)
        ns = models.Notification.all()
        assert len(ns) == 1

        n = ns[0]
        assert n.who == "publisher", "Expected: {}, Received: {}".format("publisher", n.who)
        assert n.created_by == ApplicationPublisherRevisionNotify.ID, "Expected: {}, Received: {}".format(ApplicationPublisherRevisionNotify.ID, n.created_by)
        assert n.classification == constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE, "Expected: {}, Received: {}".format(constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE, n.classification)
        assert n.long is not None
        assert n.short is not None
        assert n.action is None
        assert not n.is_seen()

    def test_consume_fail(self):
        event = models.Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED, context={"application": {"dummy" : "data"}})
        with self.assertRaises(exceptions.NoSuchObjectException):
            ApplicationPublisherRevisionNotify.consume(event)

