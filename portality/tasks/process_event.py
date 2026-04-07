from portality.background import BackgroundTask
from portality.core import app
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import events_queue
from portality import models
from portality.bll import DOAJ
import json


class ProcessEventBackgroundTask(BackgroundTask):
    """
    Background task for processing events asynchronously.
    """
    __action__ = "process_event"

    def post_execute(self):
        """
        Override default post-execution to do nothing.
        We intentionally avoid triggering BACKGROUND_JOB_FINISHED for this task,
        as it is itself processing events and should not emit another event.
        """
        return

    def run(self):
        """
        Execute the task as specified by the background_job
        """
        job = self.background_job
        params = job.params

        # Get the serialized event from the job parameters
        serialized_event = self.get_param(params, "serialized_event")
        if not serialized_event:
            raise Exception("No serialized event found in job parameters")

        # Deserialize the event
        event_data = json.loads(serialized_event)
        event = models.Event(raw=event_data)

        # Get the events service and consume the event
        events_service = DOAJ.eventsService()
        events_service.consume(event)

        # Record a successful completion
        job.add_audit_message("Event processed successfully")

    def cleanup(self):
        """
        Cleanup after a successful OR failed run of the task
        """
        pass  # No cleanup needed for this task

    @classmethod
    def prepare(cls, username, **kwargs):
        """
        Take an arbitrary set of keyword arguments and return an instance of a BackgroundJob,
        or fail with a suitable exception

        :param username: the user creating the job
        :param kwargs: arbitrary keyword arguments pertaining to this task type
        :return: a BackgroundJob instance representing this task
        """
        event = kwargs.get("event")
        if not event:
            raise Exception("No event provided to ProcessEventBackgroundTask.prepare")

        # Serialize the event
        serialized_event = event.serialise()

        # Create a job with the serialized event
        params = cls.create_job_params(
            serialized_event=serialized_event
        )

        # Create the background job
        job = background_helper.create_job(
            username=username,
            action=cls.__action__,
            queue_id=background_helper.get_queue_id_by_task_queue(events_queue),
            task_queue=events_queue,
            params=params
        )

        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_helper.submit_by_background_job(
            background_job,
            process_event_execute
        )


# Create a helper for the task
process_event_task_helper = ProcessEventBackgroundTask.create_huey_helper(events_queue)


# Register the execute function
@process_event_task_helper.register_execute()
def process_event_execute(job_id):
    process_event_task_helper.execute_common(job_id)