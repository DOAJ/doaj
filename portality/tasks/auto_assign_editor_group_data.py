from portality import models
from portality.background import BackgroundTask, BackgroundApi
from portality.bll import DOAJ, exceptions
from portality.core import app
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import scheduled_short_queue as queue

class AutoAssignEditorGroupDataTask(BackgroundTask):

    __action__ = "auto_assign_editor_group_data"

    def run(self):
        """
        Execute the task as specified by the background_job 
        :return:
        """

        params = self.background_job.params
        prune = self.get_param(params, "prune", True)

        try:
            routers = DOAJ.applicationService().retrieve_ur_editor_group_sheets(keep_history=2 if prune else -1)
        except exceptions.RemoteServiceException as e:
            msg = "Failed to retrieve data from google sheets: " + str(e)
            self.background_job.add_audit_message(msg)
            self.background_job.fail()
            DOAJ.adminAlertsService().alert("bg." + self.__action__, msg)
            return
        except ValueError as e:
            msg = "At least some of the data was invalid: " + str(e)
            self.background_job.add_audit_message(msg)
            self.background_job.fail()
            DOAJ.adminAlertsService().alert("bg." + self.__action__, msg)
            return

        self.background_job.add_audit_message("Latest mapping sheets retrieved and loaded; {x} rules loaded".format(x=len(routers)))

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
        prune = kwargs.get("prune", True)
        params = {}
        cls.set_param(params, "prune", prune)

        # prepare a job record
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
        auto_assign_editor_group_data.schedule(args=(background_job.id,), delay=10)


huey_helper = AutoAssignEditorGroupDataTask.create_huey_helper(queue)


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
