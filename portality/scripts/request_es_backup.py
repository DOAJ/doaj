from portality.core import app
from portality.tasks import request_es_backup
from portality.background import BackgroundApi

if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print("System is in READ-ONLY mode, confirm to continue")
        if input("Continue? y/N: ").lower() != 'y':
            exit()

    user = app.config.get("SYSTEM_USERNAME")
    job = request_es_backup.RequestESBackupBackgroundTask.prepare(user)
    task = request_es_backup.RequestESBackupBackgroundTask(job)
    BackgroundApi.execute(task)
