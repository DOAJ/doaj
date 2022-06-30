from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from portality.events.consumers.update_request_publisher_assigned_notify import UpdateRequestPublisherAssignedNotify
from doajtest.fixtures import ApplicationFixtureFactory
import time


class TestApplicationPublisherAssignedNotify(DoajTestCase):
    def setUp(self):
        super(TestApplicationPublisherAssignedNotify, self).setUp()

    def tearDown(self):
        super(TestApplicationPublisherAssignedNotify, self).tearDown()

    def test_consumes(self):
        source = ApplicationFixtureFactory.make_application_source()

        event = models.Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED, context={"application" : source, "old_editor": "", "new_editor" : source["admin"]["editor"]})
        assert UpdateRequestPublisherAssignedNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED,
                             context={"application": source, "old_editor": "editor"})
        assert not UpdateRequestPublisherAssignedNotify.consumes(event)

        event = models.Event("test:event", context={"application" : source})
        assert not UpdateRequestPublisherAssignedNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED)
        assert not UpdateRequestPublisherAssignedNotify.consumes(event)

    def test_consume_success(self):
        self._make_and_push_test_context("/")

        source = ApplicationFixtureFactory.make_application_source()
        app = models.Application(**source)
        # app.save()

        acc = models.Account()
        acc.set_id(app.owner)
        acc.set_email("test@example.com")
        acc.save(blocking=True)

        event = models.Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED, context={"application" : app.data, "old_editor": "", "new_editor": app.editor})
        UpdateRequestPublisherAssignedNotify.consume(event)

        time.sleep(2)
        ns = models.Notification.all()
        assert len(ns) == 1

        n = ns[0]
        assert n.who == app.owner
        assert n.created_by == UpdateRequestPublisherAssignedNotify.ID
        assert n.classification == constants.NOTIFICATION_CLASSIFICATION_ASSIGN
        assert n.long is not None
        assert n.short is not None
        assert n.action is None
        assert not n.is_seen()

    def test_consume_fail(self):
        event = models.Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED, context={"application": {"key" : "value"}})
        with self.assertRaises(exceptions.NoSuchObjectException):
            UpdateRequestPublisherAssignedNotify.consume(event)

        source = ApplicationFixtureFactory.make_application_source()
        del source["admin"]["owner"]
        app = models.Application(**source)
        # app.save(blocking=True)

        event = models.Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED, context={"application": app.data})
        with self.assertRaises(exceptions.NoSuchPropertyException):
            UpdateRequestPublisherAssignedNotify.consume(event)
