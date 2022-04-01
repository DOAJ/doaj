from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from portality.events.consumers.application_assed_assigned_notify import ApplicationAssedAssignedNotify
from doajtest.fixtures import ApplicationFixtureFactory
import time


class TestApplicationAssedAssignedNotify(DoajTestCase):
    def setUp(self):
        super(TestApplicationAssedAssignedNotify, self).setUp()

    def tearDown(self):
        super(TestApplicationAssedAssignedNotify, self).tearDown()

    def test_consumes(self):
        event = models.Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED, context={"application" : "2345"})
        assert ApplicationAssedAssignedNotify.consumes(event)

        event = models.Event("test:event", context={"application" : "2345"})
        assert not ApplicationAssedAssignedNotify.consumes(event)

        event = models.Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED)
        assert not ApplicationAssedAssignedNotify.consumes(event)

    def test_consume_success(self):
        self._make_and_push_test_context("/")

        source = ApplicationFixtureFactory.make_application_source()
        app = models.Application(**source)
        app.save()

        acc = models.Account()
        acc.set_id(app.editor)
        acc.set_email("test@example.com")
        acc.save(blocking=True)

        event = models.Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED, context={"application" : app.id})
        ApplicationAssedAssignedNotify.consume(event)

        time.sleep(2)
        ns = models.Notification.all()
        assert len(ns) == 1

        n = ns[0]
        assert n.who == app.editor
        assert n.created_by == ApplicationAssedAssignedNotify.ID
        assert n.classification == constants.NOTIFICATION_CLASSIFICATION_ASSIGN
        assert n.message is not None
        assert n.action is not None
        assert not n.is_seen()

    def test_consume_fail(self):
        event = models.Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED, context={"application": "abcd"})
        with self.assertRaises(exceptions.NoSuchObjectException):
            ApplicationAssedAssignedNotify.consume(event)

        source = ApplicationFixtureFactory.make_application_source()
        del source["admin"]["editor"]
        app = models.Application(**source)
        app.save(blocking=True)

        event = models.Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED, context={"application": app.id})
        with self.assertRaises(exceptions.NoSuchPropertyException):
            ApplicationAssedAssignedNotify.consume(event)
