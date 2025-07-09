from portality.core import app
from portality.tasks.process_event import ProcessEventBackgroundTask


def send_event(event):
    """
    Send an event to be processed asynchronously by creating and submitting a background job.
    
    :param event: The event to be processed
    """
    # Get the system username for creating the background job
    username = app.config.get("SYSTEM_USERNAME")
    
    # Create and submit a background job for processing the event
    job = ProcessEventBackgroundTask.prepare(username, event=event)
    ProcessEventBackgroundTask.submit(job)