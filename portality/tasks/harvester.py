from portality import models
from portality.background import BackgroundTask, BackgroundApi

from portality.tasks.harvester_helpers import workflow
from portality.core import app
from portality.models.harvester import HarvesterProgressReport as Report
from portality.tasks.redis_huey import schedule, long_running
from portality.decorators import write_required

import datetime


class BGHarvesterLogger(object):
    def __init__(self, job):
        self._job = job

    def log(self, msg):
        self._job.add_audit_message(msg)


class HarvesterBackgroundTask(BackgroundTask):
    mail_prereqs = False
    __action__ = "harvest"

    def run(self):
        """
        Execute the task as specified by the background_job
        :return:
        """

        if not self.only_me():
            self.background_job.add_audit_message("Another harvester is currently running, skipping this run")
            return

        logger = BGHarvesterLogger(self.background_job)
        accs = list(app.config.get("HARVESTER_API_KEYS", {}).keys())
        harvester_workflow = workflow.HarvesterWorkflow(logger)
        for account_id in accs:
            harvester_workflow.process_account(account_id)

        report = Report.write_report()
        self.background_job.add_audit_message(report)

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
        background_job.save()
        harvest.schedule(args=(background_job.id,), delay=10)
        # fixme: schedule() could raise a huey.exceptions.HueyException and not reach redis- would that be logged?

    def only_me(self):
        return not models.BackgroundJob.has_active(self.__action__)


@long_running.periodic_task(schedule("harvest"))
@write_required(script=True)
def scheduled_harvest():
    user = app.config.get("SYSTEM_USERNAME")
    job = HarvesterBackgroundTask.prepare(user)
    HarvesterBackgroundTask.submit(job)

@long_running.task()
@write_required(script=True)
def harvest(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = HarvesterBackgroundTask(job)
    BackgroundApi.execute(task)
