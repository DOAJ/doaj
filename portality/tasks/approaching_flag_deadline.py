import time

from portality.core import app
from portality.bll import DOAJ
from portality.lib import dates
from portality import models
from portality.util import url_for

from portality.tasks.redis_huey import scheduled_short_queue as queue

from portality.background import BackgroundTask, BackgroundApi
from portality.tasks.helpers import background_helper
from portality.ui.messages import Messages
from portality import constants


class ApproachingDeadlineQuery:
    def __init__(self):
        self._delta = app.config.get('FLAG_APPROACHING_DEADLINE_DELTA', 7)
        self._ddate = dates.days_after_now(days=self._delta)

    def query(self):
        return {
            "query": {
                "bool": {
                    "filter": {
                        "bool": {
                            "must": [
                                {"term": {"index.most_urgent_flag_deadline": dates.format(self._ddate, format="%Y-%m-%d")}},
                                {"term": {"admin.in_doaj": True}}
                            ]
                        }
                    }
                }
            }
        }


# ~~FindFlagsWithApproachingDeadlineTask:Task~~
class ApproachingFlagDeadlineTask(BackgroundTask):
    __action__ = "approaching_flag_deadline"

    def __init__(self, job):
        super(ApproachingFlagDeadlineTask, self).__init__(job)
        self._delta = app.config.get('FLAG_APPROACHING_DEADLINE_DELTA', 7)
        self._ddate = dates.days_after_now(days=self._delta)

    def find_journals_with_approaching_deadlines(self):
        jdata = []

        for journal in models.Journal.iterate(q=ApproachingDeadlineQuery().query(), keepalive='5m', wrap=True):
            # ~~->Journal:Model~~
            jdata.append(journal.id)
            self.background_job.add_audit_message(Messages.JOURNALS_WITH_APPROACHING_DEADLINES_FOUND.format(delta=self._delta, id=journal.id))

        return jdata

    def run(self):
        journals = self.find_journals_with_approaching_deadlines()
        if len(journals):
            for j in journals:
                journal = models.Journal.pull(j)
                assignee = journal.flags[0]["flag"]["assigned_to"]

                svc = DOAJ.notificationsService()

                acc = models.Account.pull(assignee)
                if acc is None:
                    self.background_job.add_audit_message(Messages.EXCEPTION_NOTIFICATION_NO_ACCOUNT.format(x=assignee))
                    continue

                notification = models.Notification()
                notification.classification = constants.NOTIFICATION_CLASSIFICATION_STATUS
                notification.who = acc.id

                source_id = "bg:job:" + self.__action__ + ":notify"

                notification.created_by = source_id
                notification.long = svc.long_notification(source_id).format(
                    journal_title=journal.bibjson().title,
                    id=journal.id)

                notification.short = svc.short_notification(source_id)
                notification.action = url_for("admin.journal_page", journal_id=journal.id)

                svc.notify(notification)

            self.background_job.add_audit_message(Messages.JOURNALS_WITH_APPROACHING_DEADLINES_FOUND_NOTIFICATION_SENT_LOG)
        else:
            self.background_job.add_audit_message(Messages.NO_JOURNALS_WITH_APPROACHING_DEADLINES_FOUND_LOG)

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

        :param username: User account for this task to complete as
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
        approaching_flag_deadline.schedule(args=(background_job.id,), delay=app.config.get('HUEY_ASYNC_DELAY', 10))


huey_helper = ApproachingFlagDeadlineTask.create_huey_helper(queue)


@huey_helper.register_schedule
def scheduled_approaching_flag_deadline():
    user = app.config.get("SYSTEM_USERNAME")
    job = ApproachingFlagDeadlineTask.prepare(user)
    ApproachingFlagDeadlineTask.submit(job)


@huey_helper.register_execute(is_load_config=False)
def approaching_flag_deadline(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = ApproachingFlagDeadlineTask(job)
    BackgroundApi.execute(task)
