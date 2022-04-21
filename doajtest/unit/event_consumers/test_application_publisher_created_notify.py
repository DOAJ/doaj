from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from portality.events.consumers.application_publisher_created_notify import ApplicationPublisherCreatedNotify
from doajtest.fixtures import ApplicationFixtureFactory
import time


class TestApplicationPublisherCreatedNotify(DoajTestCase):
    def setUp(self):
        super(TestApplicationPublisherCreatedNotify, self).setUp()

    def tearDown(self):
        super(TestApplicationPublisherCreatedNotify, self).tearDown()

    def test_consumes(self):
        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application" :"2345", "status": "created"})
        assert ApplicationPublisherCreatedNotify.consumes(event)

        event = models.Event("test:event", context={"application" : "2345"})
        assert not ApplicationPublisherCreatedNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_STATUS)
        assert not ApplicationPublisherCreatedNotify.consumes(event)

    def test_consume_success(self):
        self._make_and_push_test_context("/")
        source = ApplicationFixtureFactory.make_application_source()
        app = models.Application(**source)
        app.set_id("1234")
        app.save()

        acc = models.Account()
        acc.set_id("publisher")
        acc.set_email("test@example.com")
        acc.save()

        app.set_owner(acc.id)

        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application" : app, "status": "created"})
        ApplicationPublisherCreatedNotify.consume(event)

        time.sleep(2)
        ns = models.Notification.all()
        assert len(ns) == 1

        n = ns[0]
        assert n.who == "publisher"
        assert n.created_by == ApplicationPublisherCreatedNotify.ID
        assert n.classification == constants.NOTIFICATION_CLASSIFICATION_CREATE
        assert n.message is not None
        assert not n.is_seen()

    def test_consume_fail(self):
        event = models.Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED, context={"application": {"test":"abcd"}})
        with self.assertRaises(exceptions.NoSuchObjectException):
            ApplicationPublisherCreatedNotify.consume(event)

