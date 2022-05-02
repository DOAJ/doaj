from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from portality.events.consumers.application_owner_accepted_notify import ApplicationOwnerAcceptedNotify
from doajtest.fixtures import ApplicationFixtureFactory
import time


class TestApplicationOwnerAcceptedNotify(DoajTestCase):
    def setUp(self):
        super(TestApplicationOwnerAcceptedNotify, self).setUp()

    def tearDown(self):
        super(TestApplicationOwnerAcceptedNotify, self).tearDown()

    def test_consumes(self):
        source = ApplicationFixtureFactory.make_application_source()
        source["admin"]["application_type"] = constants.APPLICATION_TYPE_NEW_APPLICATION

        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application" : source, "old_status" : "in progress", "new_status": "accepted"})
        assert ApplicationOwnerAcceptedNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_STATUS,
                             context={"application": source, "old_status": "ready", "new_status": "ready"})
        assert not ApplicationOwnerAcceptedNotify.consumes(event)

        event = models.Event("test:event", context={"application" : source})
        assert not ApplicationOwnerAcceptedNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_STATUS)
        assert not ApplicationOwnerAcceptedNotify.consumes(event)

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
        ApplicationOwnerAcceptedNotify.consume(event)

        time.sleep(2)
        ns = models.Notification.all()
        assert len(ns) == 1

        n = ns[0]
        assert n.who == "publisher"
        assert n.created_by == ApplicationOwnerAcceptedNotify.ID
        assert n.classification == constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
        assert n.message is not None
        assert n.action is not None
        assert not n.is_seen()

    def test_consume_fail(self):
        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application": {"key" : "value"}})
        with self.assertRaises(exceptions.NoSuchObjectException):
            ApplicationOwnerAcceptedNotify.consume(event)

