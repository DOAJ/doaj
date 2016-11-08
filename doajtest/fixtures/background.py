from copy import deepcopy
from portality.background import BackgroundTask
from portality import models

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
    "id" : "123456789",
    "created_date" : "2001-01-01T00:00:00Z",
    "last_updated" : "2001-01-02T00:00:00Z",
    "status" : "queued",
    "user" : "testuser",
    "queue_id" : "abcdef",
    "action" : "status_change",
    "params" : {},
    "reference" : {},
    "audit" : [
        {"message" : "created job", "timestamp" : "2001-01-01T00:00:00Z"}
    ]
}