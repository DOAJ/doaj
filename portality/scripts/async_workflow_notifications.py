"""A manual trigger for editorial notification emails to managing editors, editors and associate editors."""

from portality.core import app
from portality.tasks import async_workflow_notifications
from portality.background import BackgroundApi

if __name__ == "__main__":
    user = app.config.get("SYSTEM_USERNAME")
    if user is None:
        print ("System user not specified. Set SYSTEM_USERNAME in config file to run this script.")
        exit(1)
    else:
        job = async_workflow_notifications.AsyncWorkflowBackgroundTask.prepare(user)
        task = async_workflow_notifications.AsyncWorkflowBackgroundTask(job)
        BackgroundApi.execute(task)
