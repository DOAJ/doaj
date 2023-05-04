from datetime import datetime, timedelta

from esprit.raw import Connection
from esprit.snapshot import ESSnapshotsClient

from portality import models
from portality.background import BackgroundTask, BackgroundApi
from portality.core import app
from portality.lib import dates
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import long_running


# FIXME: update for index-per-type


class PruneESBackupsBackgroundTask(BackgroundTask):

    __action__ = "prune_es_backups"

    def run(self):
        """
        Execute the task as specified by the background_job
        :return:
        """
        job = self.background_job

        # Connection to the ES index
        conn = Connection(app.config.get("ELASTIC_SEARCH_HOST"), index='_snapshot')

        snap_ttl = app.config.get('ELASTIC_SEARCH_SNAPSHOT_TTL', 366)
        snap_thresh = dates.now() - timedelta(days=snap_ttl)
        job.add_audit_message('Deleting backups older than {}'.format(dates.format(snap_thresh)))

        client = ESSnapshotsClient(conn, app.config['ELASTIC_SEARCH_SNAPSHOT_REPOSITORY'])
        client.prune_snapshots(snap_ttl, self.report_deleted_closure(job))

    def cleanup(self):
        """
        Cleanup after a successful OR failed run of the task
        :return:
        """
        pass

    @staticmethod
    def report_deleted_closure(job):
        """ Report the deletion to the background task audit log """
        def _report_deleted_callback(snapshot, status_code, result):
            job.add_audit_message('Deleted snapshot {0}, Status code: {1}, Successful: {2}'.format(snapshot.name, status_code, result))

        return _report_deleted_callback

    @classmethod
    def prepare(cls, username, **kwargs):
        """
        Take an arbitrary set of keyword arguments and return an instance of a BackgroundJob,
        or fail with a suitable exception

        :param username: The user this job will run under
        :param kwargs: arbitrary keyword arguments pertaining to this task type
        :return: a BackgroundJob instance representing this task
        """

        # first prepare a job record
        job = background_helper.create_job(username, cls.__action__,
                                           queue_id=huey_helper.queue_id)
        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_job.save()
        prune_es_backups.schedule(args=(background_job.id,), delay=10)


huey_helper = PruneESBackupsBackgroundTask.create_huey_helper(long_running)


@huey_helper.register_schedule
def scheduled_prune_es_backups():
    user = app.config.get("SYSTEM_USERNAME")
    job = PruneESBackupsBackgroundTask.prepare(user)
    PruneESBackupsBackgroundTask.submit(job)


@huey_helper.register_execute(is_load_config=False)
def prune_es_backups(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = PruneESBackupsBackgroundTask(job)
    BackgroundApi.execute(task)
