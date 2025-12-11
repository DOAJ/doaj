from portality import models
from portality.background import BackgroundTask, BackgroundApi
from portality.bll.doaj import DOAJ
from portality.core import app
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import scheduled_long_queue as queue
from portality.bll.services.export import RISExportReporter

class RISExportBackgroundTaskReporter(RISExportReporter):
    def __init__(self, job):
        super().__init__()
        self._job = job

    def processed(self, total_so_far):
        super().processed(total_so_far)
        if self._processed % 10000 == 0:
            self.msg(f"Processed {self._processed} articles so far; {self._loaded} RIS exports generated.")

    def msg(self, message):
        self._job.add_audit_message(message)


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

        job.add_audit_message("Starting RIS Update")
        exportSvc.bulk_generate_ris(force_update=force_update, reporter=RISExportBackgroundTaskReporter(job))
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
