from portality.core import app
import redis


class ConcurrencyPreventionService:
    def __init__(self):
        self.rs = redis.Redis(host=app.config.get("REDIS_HOST"), port=app.config.get("REDIS_PORT"))

    def check_concurrency(self, key, _id):
        """
        Checks whether concurrent request has been submitted
        Returns true if clash is detected
        """
        value = self.rs.get(key)
        return value is not None and value != _id

    def store_concurrency(self, key, _id, timeout=None):
        if timeout is None:
            timeout = app.config.get("UR_CONCURRENCY_TIMEOUT", 10)
        if timeout > 0:
            self.rs.set(key, _id, ex=timeout)
