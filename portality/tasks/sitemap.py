from portality import models
from portality.bll.services.audit import AuditBuilder
from portality.core import app

from portality.tasks.redis_huey import main_queue, schedule
from portality.decorators import write_required

from portality.background import BackgroundTask, BackgroundApi, BackgroundException

from portality.bll.doaj import DOAJ

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
        job = models.BackgroundJob()
        job.user = username
        job.action = cls.__action__
        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        AuditBuilder(f'create bgjob {__name__}', target_obj=background_job).save()
        background_job.save()
        generate_sitemap.schedule(args=(background_job.id,), delay=10)


@main_queue.periodic_task(schedule("sitemap"))
@write_required(script=True)
def scheduled_sitemap():
    user = app.config.get("SYSTEM_USERNAME")
    job = SitemapBackgroundTask.prepare(user)
    SitemapBackgroundTask.submit(job)


@main_queue.task()
@write_required(script=True)
def generate_sitemap(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = SitemapBackgroundTask(job)
    BackgroundApi.execute(task)
