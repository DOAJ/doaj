from datetime import datetime

from portality import models
from portality.background import BackgroundTask, BackgroundApi, BackgroundException
from portality.core import app
from portality.lib import dates
from portality.models.harvester import HarvesterProgressReport as Report
from portality.store import StoreFactory
from portality.tasks.harvester_helpers import workflow
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import long_running


class BGHarvesterLogger(object):
    def __init__(self, job):
        self._job = job

        self._logFile = "harvest-" + job.id + ".log"
        tempStore = StoreFactory.tmp()
        self._tempFile = tempStore.path(app.config.get("STORE_HARVESTER_CONTAINER"), self._logFile, create_container=True, must_exist=False)
        self._job.add_audit_message("Audit messages for this run will be stored in file {x}".format(x=self._tempFile))
        self._job.save()

        self._fh = open(self._tempFile, "w")

    def log(self, msg):
        # self._job.add_audit_message(msg)
        self._fh.write("[{d}] {m}\n".format(d=dates.now_str(), m=msg))

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
        return background_helper.create_job(username, cls.__action__, queue_id=huey_helper.queue_id)

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
        age = app.config.get("HARVESTER_ZOMBIE_AGE")
        since = dates.format(dates.before_now(age))
        actives = models.BackgroundJob.active(self.__action__, since=since)
        if self.background_job.id in [a.id for a in actives] and len(actives) == 1:
            return True
        if len(actives) == 0:
            return True
        return False


huey_helper = HarvesterBackgroundTask.create_huey_helper(long_running)


@huey_helper.register_schedule
def scheduled_harvest():
    user = app.config.get("SYSTEM_USERNAME")
    job = HarvesterBackgroundTask.prepare(user)
    HarvesterBackgroundTask.submit(job)


@huey_helper.register_execute(is_load_config=False)
def harvest(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = HarvesterBackgroundTask(job)
    BackgroundApi.execute(task)
