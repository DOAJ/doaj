from portality import models
from portality.core import app

from portality.tasks.redis_huey import main_queue, schedule
from portality.decorators import write_required

from portality.background import BackgroundTask, BackgroundApi, BackgroundException
from portality.journalcsv import make_journals_csv

import os, codecs
from datetime import datetime
from operator import itemgetter


class JournalCSVBackgroundTask(BackgroundTask):

    __action__ = "journal_csv"

    def run(self):
        """
        Execute the task as specified by the background_job 
        :return:
        """
        job = self.background_job

        cdir = app.config.get("CACHE_DIR")
        if cdir is None:
            raise BackgroundException("You must set CACHE_DIR in the config")
        csvdir = os.path.join(cdir, "csv")

        if not os.path.exists(csvdir):
            os.makedirs(csvdir)

        # save it into the cache directory
        attachment_name = 'doaj_' + datetime.strftime(datetime.now(), '%Y%m%d_%H%M') + '_utf8.csv'
        out = os.path.join(csvdir, attachment_name)

        # write the csv file
        with codecs.open(out, 'wb', encoding='utf-8') as csvfile:
            make_journals_csv(csvfile)

        # update the ES record to point to the new file
        models.Cache.cache_csv(attachment_name)

        # remove all but the two latest csvs
        csvs = [(c, os.path.getmtime(os.path.join(csvdir, c))) for c in os.listdir(csvdir) if c.endswith(".csv")]
        sorted_csvs = sorted(csvs, key=itemgetter(1), reverse=True)

        if len(sorted_csvs) > 2:
            for c, lm in sorted_csvs[2:]:
                os.remove(os.path.join(csvdir, c))

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
        cdir = app.config.get("CACHE_DIR")
        if cdir is None:
            raise BackgroundException("You must set CACHE_DIR in the config")

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
        journal_csv.schedule(args=(background_job.id,), delay=10)


@main_queue.periodic_task(schedule("journal_csv"))
@write_required(script=True)
def scheduled_journal_csv():
    user = app.config.get("SYSTEM_USERNAME")
    job = JournalCSVBackgroundTask.prepare(user)
    JournalCSVBackgroundTask.submit(job)


@main_queue.task()
@write_required(script=True)
def journal_csv(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = JournalCSVBackgroundTask(job)
    BackgroundApi.execute(task)
