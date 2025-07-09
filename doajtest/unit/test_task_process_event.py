from unittest.mock import patch, MagicMock
import json

from doajtest.helpers import DoajTestCase
from portality import models
from portality.bll import DOAJ
from portality.tasks.process_event import ProcessEventBackgroundTask
from portality.events.background import send_event
from doajtest.mocks.events_Consumer import MockConsumer
from portality.bll.services.events import EventsService


class TestProcessEventBackgroundTask(DoajTestCase):

    def setUp(self):
        super(TestProcessEventBackgroundTask, self).setUp()

        # Save the original event consumers and replace with our mock
        self.event_consumers = EventsService.EVENT_CONSUMERS
        EventsService.EVENT_CONSUMERS = [MockConsumer]
        MockConsumer.reset()

    def tearDown(self):
        super(TestProcessEventBackgroundTask, self).tearDown()

        # Restore the original event consumers
        EventsService.EVENT_CONSUMERS = self.event_consumers
        MockConsumer.reset()

    def test_01_prepare(self):
        """Test that the prepare method correctly creates a background job with the serialized event"""
        # Create a test event
        event = models.Event("test:event", "testuser")

        # Call prepare
        job = ProcessEventBackgroundTask.prepare("testuser", event=event)

        # Check that the job was created correctly
        assert job is not None
        assert job.user == "testuser"
        assert job.action == "process_event"

        # Check that the event was serialized and stored in the job parameters
        serialized_event = job.params.get("process_event__serialized_event")
        assert serialized_event is not None

        # Deserialize the event and check it matches the original
        event_data = json.loads(serialized_event)
        assert event_data.get("id") == "test:event"
        assert event_data.get("who") == "testuser"

    @patch('portality.tasks.process_event.DOAJ')
    def test_02_run(self, mock_doaj):
        """Test that the run method correctly processes the event"""
        # Create a mock events service
        mock_events_service = MagicMock()
        mock_doaj.eventsService.return_value = mock_events_service

        # Create a test event
        event = models.Event("test:event", "testuser")
        serialized_event = event.serialise()

        # Create a job with the serialized event
        job = models.BackgroundJob()
        job.params = {"process_event__serialized_event": serialized_event}

        # Create the task and run it
        task = ProcessEventBackgroundTask(job)
        task.run()

        # Check that the events service was called to consume the event
        mock_events_service.consume.assert_called_once()
        consumed_event = mock_events_service.consume.call_args[0][0]
        assert consumed_event.id == "test:event"
        assert consumed_event.who == "testuser"

    @patch('portality.tasks.helpers.background_helper.submit_by_background_job')
    def test_03_submit(self, mock_submit):
        """Test that the submit method correctly submits the job"""
        # Create a test job
        job = models.BackgroundJob()
        job.action = "process_event"

        # Submit the job
        ProcessEventBackgroundTask.submit(job)

        # Check that submit_by_background_job was called with the correct arguments
        mock_submit.assert_called_once()
        args, kwargs = mock_submit.call_args
        assert args[0] == job
        # The second argument could be a function or a TaskWrapper object
        # We just check that it was called with something (we can't easily check what it is)

    @patch('portality.events.background.ProcessEventBackgroundTask')
    def test_04_send_event(self, mock_task_class):
        """Test that the send_event function correctly creates and submits a job"""
        # Create a mock prepare and submit methods
        mock_job = MagicMock()
        mock_task_class.prepare.return_value = mock_job

        # Create a test event
        event = models.Event("test:event", "testuser")

        # Call send_event
        with patch('portality.events.background.app') as mock_app:
            mock_app.config.get.return_value = "system_user"
            send_event(event)

        # Check that prepare and submit were called with the correct arguments
        mock_task_class.prepare.assert_called_once()
        assert mock_task_class.prepare.call_args[0][0] == "system_user"
        assert mock_task_class.prepare.call_args[1]["event"] == event

        mock_task_class.submit.assert_called_once_with(mock_job)

    def test_05_integration(self):
        """Test the full integration of the background task with the events system"""
        # Create a test event
        event = models.Event("test:event", "testuser")

        # Create a job with the serialized event
        job = ProcessEventBackgroundTask.prepare("testuser", event=event)

        # Create the task and run it
        task = ProcessEventBackgroundTask(job)
        task.run()

        # Check that the event was consumed by our mock consumer
        assert len(MockConsumer.CONSUMED) == 1
        assert MockConsumer.CONSUMED[0].id == "test:event"
        assert MockConsumer.CONSUMED[0].who == "testuser"
