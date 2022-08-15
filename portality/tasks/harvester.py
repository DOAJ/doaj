from portality import models
from portality.background import BackgroundTask, BackgroundApi, BackgroundException
from portality.bll.services.audit import AuditBuilder

from portality.tasks.harvester_helpers import workflow
from portality.core import app
from portality.models.harvester import HarvesterProgressReport as Report
from portality.tasks.redis_huey import schedule, long_running
from portality.decorators import write_required
from portality.lib import dates
from portality.store import StoreFactory

from datetime import datetime


class BGHarvesterLogger(object):
    def __init__(self, job):
        self._job = job
        audit_builder = AuditBuilder(f'update bgjob {__name__}', target_obj=self._job)

        self._logFile = "harvest-" + job.id + ".log"
        tempStore = StoreFactory.tmp()
        self._tempFile = tempStore.path(app.config.get("STORE_HARVESTER_CONTAINER"), self._logFile, create_container=True, must_exist=False)
        self._job.add_audit_message("Audit messages for this run will be stored in file {x}".format(x=self._tempFile))
        audit_builder.save()
        self._job.save()

        self._fh = open(self._tempFile, "w")

    def log(self, msg):
        # self._job.add_audit_message(msg)
        self._fh.write("[{d}] {m}\n".format(d=dates.now(), m=msg))

    def close(self):
        self._fh.close()

        mainStore = StoreFactory.get("harvester")
        mainStore.store(app.config.get("STORE_HARVESTER_CONTAINER"), self._logFile, source_path=self._tempFile)
        url = mainStore.url(app.config.get("STORE_HARVESTER_CONTAINER"), self._logFile)
        self._job.add_audit_message("Audit messages file moved to {x}".format(x=url))

        tempStore = StoreFactory.tmp()
        tempStore.delete_file(app.config.get("STORE_HARVESTER_CONTAINER"), self._logFile)


class HarvesterBackgroundTask(BackgroundTask):
    """
    ~~Harvester:BackgroundTask~~
    """
    __action__ = "harvest"

    def run(self):
        """
        Execute the task as specified by the background_job
        :return:
        """

        if not self.only_me():
            msg = "Another harvester is currently running, skipping this run"
            self.background_job.add_audit_message(msg)
            raise BackgroundException(msg)

        logger = BGHarvesterLogger(self.background_job)
        accs = app.config.get("HARVEST_ACCOUNTS", [])
        harvester_workflow = workflow.HarvesterWorkflow(logger)
        for account_id in accs:
            harvester_workflow.process_account(account_id)

        report = Report.write_report()
        logger.log(report)
        logger.close()

        # self.background_job.add_audit_message(report)

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
        AuditBuilder(f'create bgjob {__name__}', target_obj=background_job).save()
        background_job.save()
        harvest.schedule(args=(background_job.id,), delay=10)
        # fixme: schedule() could raise a huey.exceptions.HueyException and not reach redis- would that be logged?

    def only_me(self):
        age = app.config.get("HARVESTER_ZOMBIE_AGE")
        since = dates.format(dates.before(datetime.utcnow(), age))
        actives = models.BackgroundJob.active(self.__action__, since=since)
        if self.background_job.id in [a.id for a in actives] and len(actives) == 1:
            return True
        if len(actives) == 0:
            return True
        return False


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
