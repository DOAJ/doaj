from lib2to3.fixes.fix_input import context

from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from portality.events.consumers.application_assed_acceptreject_notify import ApplicationAssedAcceptRejectNotify
from doajtest.fixtures import ApplicationFixtureFactory
import time


class TestApplicationAssedAcceptRejectNotify(DoajTestCase):
    def setUp(self):
        super(TestApplicationAssedAcceptRejectNotify, self).setUp()

    def tearDown(self):
        super(TestApplicationAssedAcceptRejectNotify, self).tearDown()

    def test_should_consume(self):

        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application" : {}, "old_status" : "completed", "new_status": constants.APPLICATION_STATUS_ACCEPTED})
        assert ApplicationAssedAcceptRejectNotify.should_consume(event)

        event = models.Event(constants.EVENT_APPLICATION_STATUS,
                             context={"application": {}, "old_status": "completed", "new_status": constants.APPLICATION_STATUS_REJECTED})
        assert ApplicationAssedAcceptRejectNotify.should_consume(event)

        event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"old_status": "ready", "new_status": "ready"})
        assert not ApplicationAssedAcceptRejectNotify.should_consume(event)

        event = models.Event("test:event", context={"application" : "2345"})
        assert not ApplicationAssedAcceptRejectNotify.should_consume(event)

        event = models.Event(constants.EVENT_APPLICATION_STATUS)
        assert not ApplicationAssedAcceptRejectNotify.should_consume(event)

    def test_consume_success(self):
        with self._make_and_push_test_context_manager("/"):

            source = ApplicationFixtureFactory.make_application_source()
            app = models.Application(**source)
            app.set_application_status(constants.APPLICATION_STATUS_ACCEPTED)
            app.application_type = constants.APPLICATION_TYPE_NEW_APPLICATION
            # app.save()

            acc = models.Account()
            acc.set_id("associate")
            acc.set_email("test@example.com")
            acc.save()

            eg = models.EditorGroup()
            eg.set_name(app.editor_group)
            eg.set_maned(acc.id)
            eg.save(blocking=True)

            event = models.Event(constants.EVENT_APPLICATION_STATUS, context={"application" : app.data, "old_status": "completed", "new_status": app.application_status})
            ApplicationAssedAcceptRejectNotify.consume(event)

            time.sleep(1)
            ns = models.Notification.all()
            assert len(ns) == 1

            n = ns[0]
            assert n.who == "associate"
            assert n.created_by == ApplicationAssedAcceptRejectNotify.ID
            assert n.classification == constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
            assert n.long is not None
            assert n.short is not None
            assert n.action is not None
            assert not n.is_seen()

    def test_consume_fail(self):
        event = models.Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED, context={"application": {"key" : "value"}})
        with self.assertRaises(exceptions.NoSuchObjectException):
            ApplicationAssedAcceptRejectNotify.consume(event)

