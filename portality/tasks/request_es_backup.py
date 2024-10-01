from portality.lib.es_snapshot import ESSnapshotsClient

from portality import models, app_email
from portality.background import BackgroundTask, BackgroundApi
from portality.core import app, es_connection
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import main_queue


class RequestESBackupBackgroundTask(BackgroundTask):

    __action__ = "request_es_backup"

    def run(self):
        """
        Execute the task as specified by the background_job
        :return:
        """

        try:
            client = ESSnapshotsClient(es_connection, app.config['ELASTIC_SEARCH_SNAPSHOT_REPOSITORY'])
            resp, success = client.request_snapshot()
            if success:
                job = self.background_job
                job.add_audit_message("ElasticSearch backup requested. Response: " + resp)
            else:
                raise Exception("Exception {0} received from snapshots plugin.".format(resp))

        except Exception as e:
            app_email.send_mail(
                to=[app.config.get('ADMIN_EMAIL', 'sysadmin@cottagelabs.com')],
                fro=app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org'),
                subject='Alert: DOAJ ElasticSearch backup failure',
                msg_body="The ElasticSearch snapshot could not requested. Error: \n" + str(e)
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
        job = background_helper.create_job(username, cls.__action__,
                                           queue_id=huey_helper.queue_id, )
        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_job.save()
        request_es_backup.schedule(args=(background_job.id,), delay=10)


huey_helper = RequestESBackupBackgroundTask.create_huey_helper(main_queue)


@huey_helper.register_schedule
def scheduled_request_es_backup():
    user = app.config.get("SYSTEM_USERNAME")
    job = RequestESBackupBackgroundTask.prepare(user)
    RequestESBackupBackgroundTask.submit(job)


@huey_helper.register_execute(is_load_config=False)
def request_es_backup(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = RequestESBackupBackgroundTask(job)
    BackgroundApi.execute(task)
