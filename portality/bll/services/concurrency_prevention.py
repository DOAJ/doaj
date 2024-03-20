from portality.core import app
import redis


class ConcurrencyPreventionService():
    def __init__(self):
        self.rs = redis.Redis(host=app.config.get("REDIS_HOST"), port=app.config.get("REDIS_PORT"))

    def checkConcurrency(self, key, id):
        """
        Checks whether concurrent request has been submitted
        Returns true if clash is detected
        """
        value = self.rs.get(key)
        return value is not None and value != id

    def storeConcurrency(self, key, id, timeout=10):
        self.rs.set(key, id, ex=timeout)
