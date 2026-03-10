from portality.core import app
from portality.tasks import article_deletion_notifications
from portality.background import BackgroundApi
from portality.models.background import StdOutBackgroundJob

def main():
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print("System is in READ-ONLY mode, script cannot run")
        exit()

    user = app.config.get("SYSTEM_USERNAME")
    job = article_deletion_notifications.ArticleDeletionNotificationsBackgroundTask.prepare(user)
    job = StdOutBackgroundJob(job, force_logging=True)
    task = article_deletion_notifications.ArticleDeletionNotificationsBackgroundTask(job)
    BackgroundApi.execute(task)

if __name__ == "__main__":
    main()
