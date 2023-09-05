from portality import models
from portality.background import BackgroundTask, BackgroundApi, BackgroundException
from portality.bll.doaj import DOAJ
from portality.core import app
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import main_queue


class SitemapBackgroundTask(BackgroundTask):
    """
    ~~Sitemap:BackgroundTask~~
    """
    __action__ = "sitemap"

    def run(self):
        """
        Execute the task as specified by the background_jon
        :return:
        """
        job = self.background_job

        # ~~-> Sitemap:Feature~~
        siteService = DOAJ.siteService()
        url, action_register = siteService.sitemap()
        for ar in action_register:
            job.add_audit_message(ar)
        job.add_audit_message("Sitemap generated; will be served from {y}".format(y=url))

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

        base_url = app.config.get("BASE_URL")
        if base_url is None:
            raise BackgroundException("BASE_URL must be set in configuration before we can generate a sitemap")

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
        generate_sitemap.schedule(args=(background_job.id,), delay=10)


huey_helper = SitemapBackgroundTask.create_huey_helper(main_queue)


@huey_helper.register_schedule
def scheduled_sitemap():
    user = app.config.get("SYSTEM_USERNAME")
    job = SitemapBackgroundTask.prepare(user)
    SitemapBackgroundTask.submit(job)


@huey_helper.register_execute(is_load_config=False)
def generate_sitemap(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = SitemapBackgroundTask(job)
    BackgroundApi.execute(task)
