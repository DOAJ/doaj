from portality import models
from portality import constants
from portality.bll import exceptions
from doajtest.helpers import DoajTestCase
from portality.events.consumers.bg_job_finished_notify import BGJobFinishedNotify
from doajtest.fixtures import BackgroundFixtureFactory
import time


class TestBGJobFinishedNotify(DoajTestCase):
    def setUp(self):
        super(TestBGJobFinishedNotify, self).setUp()

    def tearDown(self):
        super(TestBGJobFinishedNotify, self).tearDown()

    def test_consumes(self):
        event = models.Event(constants.BACKGROUND_JOB_FINISHED, context={"job" : {}})
        assert BGJobFinishedNotify.consumes(event)

        event = models.Event("test:event", context={"job" : "2345"})
        assert not BGJobFinishedNotify.consumes(event)

        event = models.Event(constants.BACKGROUND_JOB_FINISHED)
        assert not BGJobFinishedNotify.consumes(event)

    def test_consume_success(self):
        self._make_and_push_test_context("/")

        source = BackgroundFixtureFactory.example()
        bj = models.BackgroundJob(**source)
        # bj.save(blocking=True)

        acc = models.Account()
        acc.set_id('testuser')
        acc.set_email("test@example.com")
        acc.add_role('admin')
        acc.save(blocking=True)

        event = models.Event(constants.BACKGROUND_JOB_FINISHED, context={"job" : bj.data})
        BGJobFinishedNotify.consume(event)

        time.sleep(2)
        ns = models.Notification.all()
        assert len(ns) == 1

        n = ns[0]
        assert n.who == acc.id
        assert n.created_by == BGJobFinishedNotify.ID
        assert n.classification == constants.NOTIFICATION_CLASSIFICATION_FINISHED
        assert n.long is not None
        assert n.short is not None
        assert n.action is not None
        assert not n.is_seen()

    def test_consume_fail(self):
        event = models.Event(constants.BACKGROUND_JOB_FINISHED, context={"job": "abcd"})
        with self.assertRaises(exceptions.NoSuchObjectException):
            BGJobFinishedNotify.consume(event)
