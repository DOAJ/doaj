from portality.core import app
from portality.bll.exceptions import ConcurrentUpdateRequestException
from portality.ui.messages import Messages
import redis


class ConcurrencyPreventionService():
    def __init__(self):
        self.rs = redis.Redis(host=app.config.get("HUEY_HOST"), port=app.config.get("HUEY_PORT"))

    def checkConcurrency(self, key, id):
        """
        Checks whether concurrent request has been submitted
        Returns true if clash is detected
        """
        value = self.rs.get(key)
        return value is not None and value != id


    def storeConcurrency(self, key, id):
        self.rs.set(key, id, ex=app.config.get("UR_CONCURRENCY_TIMEOUT", 10))
