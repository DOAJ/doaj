from flask_login import login_user

from portality.core import app
from portality import models

import traceback


class BackgroundException(Exception):
    pass

class BackgroundApi(object):

    @classmethod
    def execute(self, background_task):
        job = background_task.background_job
        ctx = None
        if job.user is not None:
            ctx = app.test_request_context("/")
            ctx.push()
            acc = models.Account.pull(job.user)     # FIXME: what happens when this is the "system" user
            if acc is not None:
                login_user(acc)

        job.start()
        job.add_audit_message("Job Started")

        try:
            background_task.run()
        except Exception as e:
            job.fail()
            job.add_audit_message("Error in Job Run")
            job.add_audit_message("Caught in job runner during run: " + traceback.format_exc())
        job.add_audit_message("Job Run Completed")

        job.add_audit_message("Cleanup Started")
        try:
            background_task.cleanup()
        except Exception as e:
            job.fail()
            job.add_audit_message("Error in Cleanup Run")
            job.add_audit_message("Caught in job runner during cleanup: " + traceback.format_exc())
        job.add_audit_message("Job Cleanup Completed")

        job.add_audit_message("Job Finished")
        if not job.is_failed():
            job.success()
        job.save()

        if ctx is not None:
            ctx.pop()

class BackgroundTask(object):
    """
    All background tasks should extend from this object and override at least the following methods:

    - run
    - cleanup
    - prepare (class method)

    """

    __action__ = None
    """ static member variable defining the name of this task """

    def __init__(self, background_job):
        self._background_job = background_job

    @property
    def background_job(self):
        return self._background_job

    def run(self):
        """
        Execute the task as specified by the background_job
        :return:
        """
        raise NotImplementedError()

    def cleanup(self):
        """
        Cleanup after a successful OR failed run of the task
        :return:
        """
        raise NotImplementedError()

    @classmethod
    def prepare(cls, username, **kwargs):
        """
        Take an arbitrary set of keyword arguments and return an instance of a BackgroundJob,
        or fail with a suitable exception

        :param user: the user creating the job
        :param kwargs: arbitrary keyword arguments pertaining to this task type
        :return: a BackgroundJob instance representing this task
        """
        raise NotImplementedError()

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        raise NotImplementedError()

    @classmethod
    def get_param(cls, params, param_name):
        return params.get('{}__{}'.format(cls.__action__, param_name))

    @classmethod
    def set_param(cls, params, param_name, value):
        params['{}__{}'.format(cls.__action__, param_name)] = value
