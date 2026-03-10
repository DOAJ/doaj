from portality import models
from portality.background import BackgroundTask, BackgroundApi
from portality.bll.doaj import DOAJ
from portality.core import app
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import scheduled_short_queue as queue

import json


class SiteStatisticsBackgroundTask(BackgroundTask):

    __action__ = "site_statistics"

    def run(self):
        """
        Execute the task as specified by the background_job 
        :return:
        """
        job = self.background_job
        siteSvc = DOAJ.siteService()

        job.add_audit_message("Starting Site Stats Cache Update")
        new_stats = siteSvc.cache_site_statistics()
        job.add_audit_message("Site Stats Cache Updated: {stats}".format(stats=json.dumps(new_stats, indent=2)))

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
        # prepare a job record
        params = {}
        job = background_helper.create_job(username, cls.__action__, queue_id=huey_helper.queue_id, params=params)
        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_job.save()
        site_statistics.schedule(args=(background_job.id,), delay=app.config.get('HUEY_ASYNC_DELAY', 10))


huey_helper = SiteStatisticsBackgroundTask.create_huey_helper(queue)


@huey_helper.register_schedule
def scheduled_site_statistics():
    user = app.config.get("SYSTEM_USERNAME")
    job = SiteStatisticsBackgroundTask.prepare(user)
    SiteStatisticsBackgroundTask.submit(job)


@huey_helper.register_execute(is_load_config=False)
def site_statistics(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = SiteStatisticsBackgroundTask(job)
    BackgroundApi.execute(task)
