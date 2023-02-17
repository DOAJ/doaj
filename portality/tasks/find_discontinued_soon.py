import datetime
import csv
import json

from portality.core import app
from portality.bll import DOAJ
from portality import models,app_email

from portality.tasks.redis_huey import main_queue

from portality.background import BackgroundTask, BackgroundSummary, BackgroundApi
from portality.tasks.helpers import background_helper
from portality.ui.messages import Messages
from portality import constants


def _date():
    return (datetime.datetime.today() + datetime.timedelta(days=app.config.get('DISCONTINUED_DATE_DELTA', 1))).strftime(
        '%Y-%m-%d')
class DiscontinuedSoonQuery:
    @classmethod
    def query(cls):
        return {
            "query": {
                "bool": {
                    "filter": {
                        "bool" : {
                            "must": [
                                {"term" : {"bibjson.discontinued_date": _date()}},
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

    def find_journals_discontinuing_soon(self, job):
        jdata = []

        for journal in models.Journal.iterate(q=DiscontinuedSoonQuery.query(), keepalive='5m', wrap=True):
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
                        "discontinue_date": _date()
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


# Test code - please do not clean up until after the tests
# def find_journals_discontinuing_soon():
#     jdata = []
#
#     for journal in models.Journal.iterate(q=DiscontinuedSoonQuery.query(), keepalive='5m', wrap=True):
#         # ~~->Journal:Model~~
#         jdata.append(journal.id)
#
#     return jdata
#
# if __name__ == "__main__":
#     journals = find_journals_discontinuing_soon()
#     if len(journals):
#         for j in journals:
#             DOAJ.eventsService().trigger(models.Event(
#                 constants.EVENT_JOURNAL_DISCONTINUING_SOON,
#                 "system",
#                 {
#                     "journal": j,
#                     "discontinue_date": _date()
#                 }))