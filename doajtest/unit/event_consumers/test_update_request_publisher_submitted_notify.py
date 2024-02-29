import time

from doajtest.helpers import DoajTestCase
from portality import constants
from portality import models
from portality.events.consumers.update_request_publisher_submitted_notify import UpdateRequestPublisherSubmittedNotify


class TestUpdateRequestPublisherSubmittedNotify(DoajTestCase):
    def setUp(self):
        super(TestUpdateRequestPublisherSubmittedNotify, self).setUp()

    def tearDown(self):
        super(TestUpdateRequestPublisherSubmittedNotify, self).tearDown()

    def test_should_consume(self):
        assert UpdateRequestPublisherSubmittedNotify.should_consume(models.Event(
            constants.EVENT_APPLICATION_UR_SUBMITTED,
            who="testuser",
        ))

    def test_should_consume__fail(self):
        # missing who
        assert not UpdateRequestPublisherSubmittedNotify.should_consume(models.Event(
            constants.EVENT_APPLICATION_UR_SUBMITTED,
        ))

        # event id mismatch
        assert not UpdateRequestPublisherSubmittedNotify.should_consume(models.Event(
            'some_other_event_id',
            who="testuser",
        ))

    def test_consume_success(self):
        acc = models.Account()
        acc.set_id("publisher")
        acc.set_email("test@example.com")
        acc.save(blocking=True)

        context: UpdateRequestPublisherSubmittedNotify.Context = {
            'application_title': "Test Application xxxxx",
            'date_applied': "1999-11-11",
            'issns': ['9999-9999'],
        }

        event = models.Event(constants.EVENT_APPLICATION_STATUS,
                             who=acc.id,
                             context=context, )
        UpdateRequestPublisherSubmittedNotify.consume(event)

        time.sleep(1)
        models.Notification.refresh()
        ns = models.Notification.all()
        assert len(ns) == 1

        n = ns[0]
        assert n.who == "publisher"
        assert n.created_by == UpdateRequestPublisherSubmittedNotify.ID
        assert n.classification == constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
        assert context['application_title'] in n.long
        assert n.short is not None
        assert not n.is_seen()
