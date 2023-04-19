from portality.core import app
from portality.bll.exceptions import ConcurrentUpdateRequestException
from portality.ui.messages import Messages
import redis


class concurrencyPreventionService(object):
    def __init__(self, **kwargs):
        self.rs = redis.Redis(host=app.config.get("HUEY_REDIS_HOST"), port=app.config.get("HUEY_REDIS_PORT"))
        self.context = kwargs["context"]
        self.kwargs = dict(kwargs)

    def prevent_concurrency(self, **kwargs):
        if (self.context == "article"):
            return
        if (self.context == "update_request"):
            return updateRequestConcurrencyPreventionService(redis_service=self.rs, **self.kwargs).prevent_concurrency()


class updateRequestConcurrencyPreventionService(object):
    def __init__(self, redis_service, **kwargs):
        self.journal = kwargs["journal"]
        self.id = kwargs["id"]
        self.rs = redis_service

    def prevent_concurrency(self):
        aid = self.rs.get(self.journal)
        if aid is not None and aid != self.id:
            raise ConcurrentUpdateRequestException(Messages.CONCURRENT_UPDATE_REQUEST)
        self.rs.set(self.journal, self.id, ex=10)