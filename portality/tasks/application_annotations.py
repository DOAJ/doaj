import constants
from portality import models
from portality.background import BackgroundTask, BackgroundApi, BackgroundException
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import long_running
from portality.bll import DOAJ


class ApplicationAnnotations(BackgroundTask):

    __action__ = "application_annotations"

    def run(self):
        """
        Execute the task as specified by the background_jon
        :return:
        """
        job = self.background_job
        params = job.params
        app_id = self.get_param(params, "application", False)
        status_on_complete = self.get_param(params, "status_on_complete", "")

        if app_id is False:
            job.add_audit_message("Application ID must be provided when creating the job")
            job.fail()
            return

        application = models.Application.pull(app_id)

        job.add_audit_message("Running application annotation for application with id {id}".format(id=app_id))

        annoSvc = DOAJ.annotationsService()
        annoSvc.annotate_application(application, logger=lambda x: job.add_audit_message(x))

        if status_on_complete != "" and status_on_complete in constants.APPLICATION_STATUSES_ALL:
            job.add_audit_message("Setting status to {x}".format(x=status_on_complete))
            application.set_application_status(status_on_complete)
            # Note: we have not locked the application
            application.save()

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

        app_id = kwargs.get("application", False)
        status_on_complete = kwargs.get("status_on_complete", "")

        if not app_id:
            raise BackgroundException("'application' ID must be provided to prepare function")

        params = {}
        cls.set_param(params, "application", app_id)
        cls.set_param(params, "status_on_complete", status_on_complete)

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
        application_annotations.schedule(args=(background_job.id,), delay=10)


huey_helper = ApplicationAnnotations.create_huey_helper(long_running)


@huey_helper.register_execute(is_load_config=True)
def application_annotations(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = ApplicationAnnotations(job)
    BackgroundApi.execute(task)
