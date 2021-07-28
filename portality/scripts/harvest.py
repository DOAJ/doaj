from portality.core import app
from portality.tasks import harvester
from portality.background import BackgroundApi
from portality.models.background import StdOutBackgroundJob

if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print("System is in READ-ONLY mode, script cannot run")
        exit()

    user = app.config.get("SYSTEM_USERNAME")
    job = harvester.HarvesterBackgroundTask.prepare(user)
    # job = StdOutBackgroundJob(job)
    task = harvester.HarvesterBackgroundTask(job)
    BackgroundApi.execute(task)
