from portality import models
from portality.background import BackgroundTask, BackgroundApi
from portality.bll.doaj import DOAJ
from portality.core import app
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import scheduled_short_queue as queue


class JournalCSVBackgroundTask(BackgroundTask):

    __action__ = "journal_csv"

    def run(self):
        """
        Execute the task as specified by the background_job 
        :return:
        """

        def logger(msg):
            self.background_job.add_audit_message(msg)

        _l = logger if app.config.get('EXTRA_JOURNALCSV_LOGGING', False) else None

        job = self.background_job

        journalService = DOAJ.journalService()
        url, action_register = journalService.csv(logger=_l)

        # Log directly to the task if we don't have extra logging configured
        if _l is None:
            for ar in action_register:
                job.add_audit_message(ar)

        job.add_audit_message("CSV generated; will be served from {y}".format(y=url))

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
        job = background_helper.create_job(username, cls.__action__, queue_id=huey_helper.queue_id)
        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_job.save()
        journal_csv.schedule(args=(background_job.id,), delay=app.config.get('HUEY_ASYNC_DELAY', 10))


huey_helper = JournalCSVBackgroundTask.create_huey_helper(queue)


@huey_helper.register_schedule
def scheduled_journal_csv():
    user = app.config.get("SYSTEM_USERNAME")
    job = JournalCSVBackgroundTask.prepare(user)
    JournalCSVBackgroundTask.submit(job)


@huey_helper.register_execute(is_load_config=False)
def journal_csv(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = JournalCSVBackgroundTask(job)
    BackgroundApi.execute(task)
