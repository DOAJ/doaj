from portality import models
from portality.core import app

from portality.tasks.redis_huey import main_queue, schedule
from portality.decorators import write_required

from portality.background import BackgroundTask, BackgroundApi
from portality import blog

class ReadNewsBackgroundTask(BackgroundTask):

    __action__ = "read_news"

    def run(self):
        """
        Execute the task as specified by the background_jon
        :return:
        """
        blog.read_feed()

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
        read_news.schedule(args=(background_job.id,), delay=10)
        # fixme: schedule() could raise a huey.exceptions.HueyException and not reach redis- would that be logged?


@main_queue.periodic_task(schedule("read_news"))
@write_required(script=True)
def scheduled_read_news():
    user = app.config.get("SYSTEM_USERNAME")
    job = ReadNewsBackgroundTask.prepare(user)
    ReadNewsBackgroundTask.submit(job)

@main_queue.task()
@write_required(script=True)
def read_news(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = ReadNewsBackgroundTask(job)
    BackgroundApi.execute(task)
