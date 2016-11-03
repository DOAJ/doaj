from copy import deepcopy

class BackgroundFixtureFactory(object):

    @classmethod
    def example(cls):
        return deepcopy(BACKGROUND_JOB)

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