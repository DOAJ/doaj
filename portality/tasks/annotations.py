from datetime import datetime

from portality import constants
from portality import models
from portality.background import BackgroundTask, BackgroundApi, BackgroundException
from portality.annotation.resource_bundle import ResourceBundle
from portality.crosswalks.application_form import ApplicationFormXWalk
from portality.core import app
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import long_running

from portality.annotation.annotators.issn_status import ISSNStatus

ANNOTATION_PLUGINS = [
    ISSNStatus()
]


class Annotations(BackgroundTask):

    __action__ = "annotations"

    def run(self):
        """
        Execute the task as specified by the background_jon
        :return:
        """
        job = self.background_job
        params = job.params
        app_id = self.get_param(params, "application", False)

        if app_id is False:
            job.add_audit_message("Application ID must be provided when creating the job")
            job.fail()
            return

        application = models.Application.pull(app_id)
        application_form = ApplicationFormXWalk.obj2form(application)
        existing_annotations = models.Annotation.for_application(app_id)
        new_annotations = models.Annotation()
        new_annotations.application = application.id
        resource_bundle = ResourceBundle()

        job.add_audit_message("Running application annotation for application with id {id}".format(id=app_id))

        if existing_annotations is None:
            job.add_audit_message("There are no existing annotations for this application")
        else:
            job.add_audit_message("There are existing annotations for this application.  Annotation id {id}".format(id=existing_annotations.id))

        # FIXME: this is where we would pass in a resource bundle
        for annotator in ANNOTATION_PLUGINS:
            job.add_audit_message("Running annotation plugin {x}".format(x=annotator.name()))
            logs = annotator.annotate(application_form, application, new_annotations, resource_bundle, existing_annotations)
            for log in logs:
                job.add_audit_message(log)

        new_annotations.save()
        job.add_audit_message("Saved new annotation document {id}".format(id=new_annotations.id))

        if existing_annotations is None:
            if application.application_status == constants.APPLICATION_STATUS_POST_SUBMISSION_REVIEW:
                if application.application_type == constants.APPLICATION_TYPE_UPDATE_REQUEST:
                    job.add_audit_message("Setting Update Request status to {x}".format(x=constants.APPLICATION_STATUS_UPDATE_REQUEST))
                    application.application_status = constants.APPLICATION_STATUS_UPDATE_REQUEST
                else:
                    job.add_audit_message("Setting New Application status to {x}".format(x=constants.APPLICATION_STATUS_PENDING))
                    application.application_status = constants.APPLICATION_STATUS_PENDING

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

        if not app_id:
            raise BackgroundException("'application' ID must be provided to prepare function")

        params = {}
        cls.set_param(params, "application", app_id)

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
        annotations.schedule(args=(background_job.id,), delay=10)


huey_helper = Annotations.create_huey_helper(long_running)


@huey_helper.register_execute(is_load_config=True)
def annotations(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = Annotations(job)
    BackgroundApi.execute(task)
