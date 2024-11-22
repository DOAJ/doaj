from portality import models
from portality.core import app
from portality.background import BackgroundTask, BackgroundApi, BackgroundException
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import long_running
from portality.bll import DOAJ

#######################################
# NOTE: this background task is currently not in use, it is prepped for being used with
# autocheck-on-demand from the administrators via the user interface, which is not yet implemented
#
# When we implement that functionality we will also need to implement tests for this
#######################################


class JournalAutochecks(BackgroundTask):

    __action__ = "journal_autochecks"

    def run(self):
        """
        Execute the task as specified by the background_jon
        :return:
        """
        job = self.background_job
        params = job.params
        journal_id = self.get_param(params, "journal", False)

        if journal_id is False:
            job.add_audit_message("Journal ID must be provided when creating the job")
            job.fail()
            return

        journal = models.Journal.pull(journal_id)

        job.add_audit_message("Running journal autocheck for journal with id {id}".format(id=journal_id))

        annoSvc = DOAJ.autochecksService()
        annoSvc.autocheck_journal(journal, logger=lambda x: job.add_audit_message(x))

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

        journal_id = kwargs.get("journal", False)

        if not journal_id:
            raise BackgroundException("'journal' ID must be provided to prepare function")

        params = {}
        cls.set_param(params, "journal", journal_id)

        # first prepare a job record
        job = background_helper.create_job(username=username,
                                           action=cls.__action__,
                                           params=params,
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
        journal_autochecks.schedule(args=(background_job.id,), delay=app.config.get('HUEY_ASYNC_DELAY', 10))


huey_helper = JournalAutochecks.create_huey_helper(long_running)


@huey_helper.register_execute(is_load_config=True)
def journal_autochecks(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = JournalAutochecks(job)
    BackgroundApi.execute(task)
