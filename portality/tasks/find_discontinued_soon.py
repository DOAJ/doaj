import datetime
import csv
import json

from portality.core import app
from portality.bll import DOAJ
from portality.lib import dates
from portality import models,app_email

from portality.tasks.redis_huey import main_queue

from portality.background import BackgroundTask, BackgroundSummary, BackgroundApi
from portality.tasks.helpers import background_helper
from portality.ui.messages import Messages
from portality import constants

class DiscontinuedSoonQuery:
    def __init__(self, time_delta=None):
        self._delta = time_delta if time_delta is not None else app.config.get('DISCONTINUED_DATE_DELTA', 0);
        self._date = dates.days_after_now(days=self._delta)
    def query(self):
        return {
            "query": {
                "bool": {
                    "filter": {
                        "bool" : {
                            "must": [
                                {"term" : {"bibjson.discontinued_date": dates.format(self._date, format="%Y-%m-%d")}},
                                {"term" : {"admin.in_doaj":True}}
                            ]
                        }
                    }
                }
            }
        }

# ~~FindDiscontinuedSoonBackgroundTask:Task~~

class FindDiscontinuedSoonBackgroundTask(BackgroundTask):
    __action__ = "find_discontinued_soon"

    def __init__(self, time_delta=None):
        self._delta = time_delta if time_delta is not None else app.config.get('DISCONTINUED_DATE_DELTA', 0);
        self._date = dates.days_after_now(days=self._delta)

    def find_journals_discontinuing_soon(self, job):
        jdata = []

        for journal in models.Journal.iterate(q=DiscontinuedSoonQuery().query(), keepalive='5m', wrap=True):
            # ~~->Journal:Model~~
            jdata.append(journal.id)
            job.add_audit_message(Messages.DISCONTINUED_JOURNAL_FOUND_LOG.format(id=journal.id))

        return jdata

    def run(self):
        job = self.background_job
        journals = self.find_journals_discontinuing_soon(job=job)
        if len(journals):
            for j in journals:
                DOAJ.eventsService().trigger(models.Event(
                    constants.EVENT_JOURNAL_DISCONTINUING_SOON,
                    "system",
                    {
                        "journal": j,
                        "discontinue_date": self._date()
                    }))
        else:
            job.add_audit_message(Messages.NO_DISCONTINUED_JOURNALS_FOUND_LOG)

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
        job = background_helper.create_job(username, cls.__action__,
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
        find_discontinued_soon.schedule(args=(background_job.id,), delay=10)

huey_helper = FindDiscontinuedSoonBackgroundTask.create_huey_helper(main_queue)

@huey_helper.register_schedule
def scheduled_find_discontinued_soon():
    user = app.config.get("SYSTEM_USERNAME")
    job = FindDiscontinuedSoonBackgroundTask.prepare(user)
    FindDiscontinuedSoonBackgroundTask.submit(job)


@huey_helper.register_execute(is_load_config=False)
def find_discontinued_soon(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = FindDiscontinuedSoonBackgroundTask(job)
    BackgroundApi.execute(task)