from portality.core import app
from portality.bll.exceptions import ConcurrentUpdateRequestException
from portality.ui.messages import Messages
import redis


class ConcurrencyPreventionService(object):
    def __init__(self, **kwargs):
        self.rs = redis.Redis(host=app.config.get("HUEY_HOST"), port=app.config.get("HUEY_PORT"))
        self.context = kwargs["context"]
        self.kwargs = dict(kwargs)

    def preventConcurrency(self, **kwargs):
        if (self.context == "article"):
            return
        if (self.context == "update_request"):
            return UpdateRequestConcurrencyPreventionService(redis_service=self.rs, **self.kwargs).preventConcurrency()


class UpdateRequestConcurrencyPreventionService(object):
    def __init__(self, redis_service, **kwargs):
        self.journal = kwargs["journal"]
        self.id = kwargs["id"]
        self.rs = redis_service

    def preventConcurrency(self):
        try:
            self._checkConcurrency()
            self._storeConcurrency()
        except ConcurrencyPreventionService as e:
            raise e

    def _checkConcurrency(self):
        aid = self.rs.get(self.journal)
        if aid is not None and aid != self.id:
            raise ConcurrentUpdateRequestException(Messages.CONCURRENT_UPDATE_REQUEST)
        return True

    def _storeConcurrency(self):
        self.rs.set(self.journal, self.id, ex=app.config.get("UR_CONCURRENCY_TIMEOUT", 10))
