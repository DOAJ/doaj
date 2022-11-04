from doajtest.helpers import DoajTestCase
from portality.bll import DOAJ
from portality import models
from doajtest.mocks.events_Consumer import MockConsumer
from portality.bll.services.events import EventsService
from io import StringIO
import logging


class TestBLLEvents(DoajTestCase):

    def setUp(self):
        super(TestBLLEvents, self).setUp()

        self.event_consumers = EventsService.EVENT_CONSUMERS
        EventsService.EVENT_CONSUMERS = [MockConsumer]
        MockConsumer.reset()

        self.svc = DOAJ.eventsService()

        # Register a new log handler so we can inspect the info logs
        self.info_stream = StringIO()
        self.read_info = logging.StreamHandler(self.info_stream)
        self.read_info.setLevel(logging.INFO)
        self.app_test.logger.addHandler(self.read_info)

    def tearDown(self):
        super(TestBLLEvents, self).tearDown()

        EventsService.EVENT_CONSUMERS = self.event_consumers
        MockConsumer.reset()

        # Blank the info_stream and remove the error handler from the app
        self.info_stream.truncate(0)
        self.app_test.logger.removeHandler(self.read_info)

    def test_01_consumed(self):
        self.svc.trigger(models.Event("test:event", "testuser"))

        assert len(MockConsumer.CONSUMED) == 1
        assert MockConsumer.CONSUMED[0].id == "test:event"

        assert len(MockConsumer.CONSUMES) == 1
        assert MockConsumer.CONSUMES[0].id == "test:event"


    def test_02_not_consumed(self):
        MockConsumer.CONSUME_RESULT = False

        self.svc.trigger(models.Event("test:event", "testuser"))

        assert len(MockConsumer.CONSUMED) == 0

        assert len(MockConsumer.CONSUMES) == 1
        assert MockConsumer.CONSUMES[0].id == "test:event"

    def test_03_consume_fail(self):
        MockConsumer.CONSUME_ERROR = "CONSUME ERROR"

        self.svc.trigger(models.Event("test:event", "testuser"))

        assert len(MockConsumer.CONSUMED) == 1
        assert MockConsumer.CONSUMED[0].id == "test:event"

        assert len(MockConsumer.CONSUMES) == 1
        assert MockConsumer.CONSUMES[0].id == "test:event"

        # Use the captured info stream to get email send logs
        info_stream_contents = self.info_stream.getvalue()
        assert "CONSUME ERROR" in info_stream_contents