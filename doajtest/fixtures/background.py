from copy import deepcopy

from portality import models
from portality.background import BackgroundTask
from portality.lib import dates
from portality.models import BackgroundJob


class BackgroundFixtureFactory(object):

    @classmethod
    def example(cls):
        return deepcopy(BACKGROUND_JOB)

    @classmethod
    def get_task(cls, user=None, run_fail=False, cleanup_fail=False):
        job = models.BackgroundJob()
        if user is not None:
            job.user = user
        return MockBackgroundTask(job, run_fail=run_fail, cleanup_fail=cleanup_fail)


class MockBackgroundTask(BackgroundTask):
    def __init__(self, background_job, run_fail=False, cleanup_fail=False):
        super(MockBackgroundTask, self).__init__(background_job)
        self.run_fail = run_fail
        self.cleanup_fail = cleanup_fail

    def run(self):
        if self.run_fail:
            raise Exception("Mock Run Failed")

    def cleanup(self):
        if self.cleanup_fail:
            raise Exception("Mock Cleanup Failed")


BACKGROUND_JOB = {
    "id": "123456789",
    "created_date": "2001-01-01T00:00:00Z",
    "last_updated": "2001-01-02T00:00:00Z",
    "status": "queued",
    "user": "testuser",
    "queue_id": "abcdef",
    "action": "status_change",
    "params": {},
    "reference": {},
    "audit": [
        {"message": "created job", "timestamp": "2001-01-01T00:00:00Z"}
    ]
}


def save_mock_bgjob(action=None, status=None, created_before_sec=0, is_save=True,
                    queue_type=None):
    bgjob = BackgroundJob()

    if action:
        from portality.tasks.journal_csv import JournalCSVBackgroundTask
        bgjob.action = JournalCSVBackgroundTask.__action__

    if status:
        bgjob._set_with_struct("status", status)

    if created_before_sec != 0:
        bgjob.set_created(dates.format(dates.before_now(created_before_sec)))

    if queue_type:
        bgjob.queue_type = queue_type

    if is_save:
        bgjob.save(blocking=True)

    return bgjob
