from portality import models
from portality.background import BackgroundTask, BackgroundApi
from portality.bll.doaj import DOAJ
from portality.core import app
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import main_queue
from portality.bll import exceptions

class AutoAssignEditorGroupDataTask(BackgroundTask):

    __action__ = "auto_assign_editor_group_data"

    def run(self):
        """
        Execute the task as specified by the background_job 
        :return:
        """

        def logger(msg):
            self.background_job.add_audit_message(msg)

        try:
            DOAJ.applicationService().retrieve_ur_editor_group_sheets()
        except exceptions.RemoteServiceException as e:
            self.background_job.add_audit_message("Failed to retrieve data from google sheets")
            self.background_job.fail()
            return
        except ValueError as e:
            self.background_job.add_audit_message("At least some of the data was invalid: " + str(e))
            self.background_job.fail()
            return

        self.background_job.add_audit_message("Latest mapping sheets retrieved")

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
        auto_assign_editor_group_data.schedule(args=(background_job.id,), delay=10)


huey_helper = AutoAssignEditorGroupDataTask.create_huey_helper(main_queue)


@huey_helper.register_schedule
def scheduled_auto_assign_editor_group_data():
    user = app.config.get("SYSTEM_USERNAME")
    job = AutoAssignEditorGroupDataTask.prepare(user)
    AutoAssignEditorGroupDataTask.submit(job)


@huey_helper.register_execute(is_load_config=False)
def auto_assign_editor_group_data(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = AutoAssignEditorGroupDataTask(job)
    BackgroundApi.execute(task)
