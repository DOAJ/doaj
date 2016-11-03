from portality import models
from portality.core import app

class BackgroundApi(object):

    @classmethod
    def execute(self, background_task):
        job = background_task.background_job
        ctx = None
        if job.user is not None:
            ctx = app.test_request_context("/")
            ctx.push()

        try:
            background_task.run()
        except:
            background_task.log()

        try:
            background_task.cleanup()
        except:
            background_task.log()

        background_task.report()
        job.save()

        if ctx is not None:
            ctx.pop()

class BackgroundTask(object):
    """
    All background tasks should extend from this object and override at least the following methods:

    - run
    - cleanup
    - report
    - log
    - prepare (class method)

    """
    def __init__(self, background_job):
        self.background_job = background_job

    def run(self):
        """
        Execute the task as specified by the background_jon
        :return:
        """
        raise NotImplementedError()

    def cleanup(self):
        """
        Cleanup after a successful OR failed run of the task
        :return:
        """
        raise NotImplementedError()

    def report(self):
        """
        Augment the background_job with information about the task run
        :return:
        """
        raise NotImplementedError()

    def log(self):
        """
        Log any exceptions or other errors in running the task
        :return:
        """
        raise NotImplementedError()

    @classmethod
    def prepare(cls, **kwargs):
        """
        Take an arbitrary set of keyword arguments and return an instance of a BackgroundJob,
        or fail with a suitable exception

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
        pass