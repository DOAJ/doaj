from portality.core import app
from portality.tasks import prune_es_backups
from portality.background import BackgroundApi

if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print ("System is in READ-ONLY mode, script cannot run")
        exit()

    user = app.config.get("SYSTEM_USERNAME")
    job = prune_es_backups.PruneESBackupsBackgroundTask.prepare(user)
    task = prune_es_backups.PruneESBackupsBackgroundTask(job)
    BackgroundApi.execute(task)
