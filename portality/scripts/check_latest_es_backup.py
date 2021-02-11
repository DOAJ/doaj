from portality.core import app
from portality.tasks import check_latest_es_backup
from portality.background import BackgroundApi

if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print "System is in READ-ONLY mode, confirm to continue"
        if raw_input("Continue? y/N: ").lower() != 'y':
            exit()

    user = app.config.get("SYSTEM_USERNAME")
    job = check_latest_es_backup.CheckLatestESBackupBackgroundTask.prepare(user)
    task = check_latest_es_backup.CheckLatestESBackupBackgroundTask(job)
    BackgroundApi.execute(task)
