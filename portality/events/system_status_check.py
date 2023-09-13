import redis
from portality import constants
from portality.core import app
from portality.lib import dates

class KafkaStatusCheck:

    def __init__(self):
        self.is_kafka_active = True
        self.time_gap = app.config['TIME_GAP_REDIS_KAFKA']
        self.last_time = dates.now()
        redis_host = app.config['HUEY_REDIS_HOST']
        redis_port = app.config['HUEY_REDIS_PORT']
        self.redis_conn = redis.StrictRedis(host=redis_host, port=redis_port, db=0)

    def is_active(self):
        if self.can_check_in_redis():
            self.is_kafka_active = self.is_kafka_active_redis()
        return self.is_kafka_active

    def can_check_in_redis(self):
        time_diff = dates.now() - self.last_time
        if time_diff.seconds > self.time_gap:
            self.last_time = dates.now()
            return True

        return False

    def is_kafka_active_redis(self):
        value = self.redis_conn.get(constants.KAFKA_ACTIVE_STATUS)
        # set the key value if not set
        if value is None:
            self.set_default_kafka_status()
            return True
        return value.decode('utf-8').lower() == "true"

    def set_default_kafka_status(self):
        self.redis_conn.set(constants.KAFKA_ACTIVE_STATUS, "true")

    def set_kafka_inactive_redis(self):
        self.redis_conn.set(constants.KAFKA_ACTIVE_STATUS, "false")
