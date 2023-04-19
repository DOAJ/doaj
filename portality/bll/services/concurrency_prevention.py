from portality.core import app
from portality.bll.exceptions import ConcurrentUpdateRequestException
from portality.ui.messages import Messages
import redis

class updateRequestConcurrencyPreventionService:
    def __init__(self):
        self.rc = redis.Redis(host=app.config.get("HUEY_REDIS_HOST"), port=app.config.get("HUEY_REDIS_PORT"))

    def prevent_concurrency(self, journal, id):
        aid = self.rc.get(journal)
        if aid is not None and aid != id:
            raise ConcurrentUpdateRequestException(Messages.CONCURRENT_UPDATE_REQUEST)
        self.rc.set(journal, id, ex=10)