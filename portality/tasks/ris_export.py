from portality import models
from portality.background import BackgroundTask, BackgroundApi
from portality.bll.doaj import DOAJ
from portality.core import app
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import scheduled_long_queue as queue

BATCH_SIZE = 1000

class RISExportBackgroundTask(BackgroundTask):

    __action__ = "ris_export"

    def run(self):
        """
        Execute the task as specified by the background_job 
        :return:
        """
        job = self.background_job
        force_update = self.get_param(job.params, "force", False)

        exportSvc = DOAJ.exportService()

        def flush_batch(batch, force=False):
            if len(batch) == 0:
                return batch

            if len(batch) < BATCH_SIZE and not force:
                return batch

            models.RISExport.bulk(batch, action="index", req_timeout=120)
            job.add_audit_message("Writing {x} RIS exports".format(x=len(batch)))
            return []

        job.add_audit_message("Starting RIS Update")

        batch = []
        count = 0
        loaded = 0
        for article in models.Article.iterall_unstable():
            count += 1
            if count % 10000 == 0:
                job.add_audit_message("{x} articles processed; {y} regenerated (loaded + queued)".format(x=count, y=loaded))
            existing = models.RISExport.pull(article.id)
            if force_update or exportSvc.has_stale_ris(article, existing):
                updated = exportSvc.ris(article, save=False)
                if existing is not None and updated.ris_raw == existing.ris_raw:
                    continue

                batch.append(updated.data)
                batch = flush_batch(batch)
                loaded += 1

        flush_batch(batch, True)

        job.add_audit_message("RIS Entries updated")

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
        cls.set_param(params, "force", kwargs.get("force", False))
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
        ris_export.schedule(args=(background_job.id,), delay=app.config.get('HUEY_ASYNC_DELAY', 10))


huey_helper = RISExportBackgroundTask.create_huey_helper(queue)


@huey_helper.register_schedule
def scheduled_ris_export():
    user = app.config.get("SYSTEM_USERNAME")
    job = RISExportBackgroundTask.prepare(user)
    RISExportBackgroundTask.submit(job)


@huey_helper.register_execute(is_load_config=False)
def ris_export(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = RISExportBackgroundTask(job)
    BackgroundApi.execute(task)
