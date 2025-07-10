import time
from copy import deepcopy

from doajtest.fixtures import ApplicationFixtureFactory
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
        # success
        source = ApplicationFixtureFactory.make_update_request_source()
        assert UpdateRequestPublisherSubmittedNotify.should_consume(models.Event(
            constants.EVENT_APPLICATION_UR_SUBMITTED,
            context={"application": source},
        ))

        # event id mismatch
        assert not UpdateRequestPublisherSubmittedNotify.should_consume(models.Event(
            'akdjlaskdjalksjdlaskjdlaks',
            context={"application": source},
        ))

        # no application in context
        assert not UpdateRequestPublisherSubmittedNotify.should_consume(models.Event(
            constants.EVENT_APPLICATION_UR_SUBMITTED,
            context={},
        ))

        # application type mismatch
        source_type_mismatch = deepcopy(source)
        source_type_mismatch['admin']['application_type'] = constants.APPLICATION_TYPE_NEW_APPLICATION
        assert not UpdateRequestPublisherSubmittedNotify.should_consume(models.Event(
            constants.EVENT_APPLICATION_UR_SUBMITTED,
            context={"application": source_type_mismatch},
        ))

        # no owner
        source_no_owner = deepcopy(source)
        source_no_owner['admin']['owner'] = None
        assert not UpdateRequestPublisherSubmittedNotify.should_consume(models.Event(
            constants.EVENT_APPLICATION_UR_SUBMITTED,
            context={"application": source_no_owner},
        ))

    def test_consume_success(self):
        acc = models.Account()
        acc.set_id("publisher")
        acc.set_email("test@example.com")
        acc.save(blocking=True)

        source = ApplicationFixtureFactory.make_application_source()
        context: UpdateRequestPublisherSubmittedNotify.Context = {
            'application': source,
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
        assert source['bibjson']['title'] in n.long
        assert n.short is not None
        assert not n.is_seen()
