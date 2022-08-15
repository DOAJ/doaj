import feedparser

from portality import models
from portality.bll.services.audit import AuditBuilder
from portality.core import app

from portality.tasks.redis_huey import main_queue, schedule
from portality.decorators import write_required

from portality.background import BackgroundTask, BackgroundApi

class FeedError(Exception):
    pass


class ReadNewsBackgroundTask(BackgroundTask):

    __action__ = "read_news"

    def run(self):
        """
        Execute the task as specified by the background_jon
        :return:
        """
        read_feed()

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
        read_news.schedule(args=(background_job.id,), delay=10)
        # fixme: schedule() could raise a huey.exceptions.HueyException and not reach redis- would that be logged?


# TODO factor this into the object above, rather than sitting out here as a function (it was migrated
# here from another file)
def read_feed():
    """~~NewsReader:Feature->News:ExternalService"""
    feed_url = app.config.get("BLOG_FEED_URL")
    if feed_url is None:
        raise FeedError("No BLOG_FEED_URL defined in settings")

    f = feedparser.parse(feed_url)
    if f.bozo > 0:
        raise FeedError(f.bozo_exception)

    for e in f.entries:
        save_entry(e)

def save_entry(entry):
    news = None
    existing = models.News.by_remote_id(entry.id)
    if len(existing) > 1:
        raise FeedError("There is more than one object with this id in the index: " + entry.id)
    elif len(existing) == 1:
        news = existing[0]
    else:
        news = models.News()
    audit_builder = AuditBuilder('save or update News', target_obj=news)

    alts = [l.get("href") for l in entry.links if l.get("rel") == "alternate"]
    if len(alts) == 0:
        raise FeedError("Unable to get url of post from link@rel=alternate")

    news.remote_id = entry.id
    news.url = alts[0]
    news.title = entry.title
    news.updated = entry.updated
    news.summary = entry.summary
    news.published = entry.published

    news.save()
    audit_builder.save()


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
