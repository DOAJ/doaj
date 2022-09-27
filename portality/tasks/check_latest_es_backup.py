from esprit.raw import Connection
from esprit.snapshot import ESSnapshotsClient

from portality import models, app_email
from portality.background import BackgroundTask, BackgroundApi
from portality.core import app
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import main_queue


class CheckLatestESBackupBackgroundTask(BackgroundTask):

    __action__ = "check_latest_es_backup"

    def run(self):
        """
        Execute the task as specified by the background_job
        :return:
        """

        # Connection to the ES index
        conn = Connection(app.config["ELASTIC_SEARCH_HOST"], index='_snapshot')

        try:
            client = ESSnapshotsClient(conn, app.config['ELASTIC_SEARCH_SNAPSHOT_REPOSITORY'])
            client.check_today_snapshot()
        except Exception as e:
            app_email.send_mail(
                to=[app.config.get('ADMIN_EMAIL', 'sysadmin@cottagelabs.com')],
                fro=app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org'),
                subject='Alert: DOAJ ElasticSearch backup failure',
                msg_body="Today's ES snapshot has not been found by the checking task. Error: \n" + str(e)
            )
            raise e

    def cleanup(self):
        """
        Cleanup after a successful OR failed run of the task
        :return:
        """
        pass

    @classmethod
    def prepare(cls, username, **kwargs):
        """
        Take an arbitrary set of keyword arguments and return an instance of a BackgroundJob,
        or fail with a suitable exception

        :param kwargs: arbitrary keyword arguments pertaining to this task type
        :return: a BackgroundJob instance representing this task
        """

        # first prepare a job record
        return background_helper.create_job(username, cls.__action__, queue_type=huey_helper.queue_type)

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_job.save()
        check_latest_es_backup.schedule(args=(background_job.id,), delay=10)


huey_helper = CheckLatestESBackupBackgroundTask.create_huey_helper(main_queue)


@huey_helper.register_schedule
def scheduled_check_latest_es_backup():
    user = app.config.get("SYSTEM_USERNAME")
    job = CheckLatestESBackupBackgroundTask.prepare(user)
    CheckLatestESBackupBackgroundTask.submit(job)


@huey_helper.register_execute(is_load_config=False)
def check_latest_es_backup(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = CheckLatestESBackupBackgroundTask(job)
    BackgroundApi.execute(task)
