"""
some function for huey background job
"""
import itertools
import pickle
import re
from typing import Iterator

import redis

from portality.core import app


class HueyJobData:

    def __init__(self, data: tuple):
        self.data = data
        self.huey_id, self.queue_name, self.schedule_time, self.retries, self.retry_delay, self.args, *_ = data

    @property
    def is_scheduled(self):
        return self.schedule_time is None

    @property
    def bgjob_action(self):
        return re.sub(r'^queue_task_(scheduled_)?', '', self.queue_name)

    @property
    def bgjob_id(self):
        if self.args:
            return self.args[0][0]
        return None

    @classmethod
    def from_redis(cls, redis_row):
        return HueyJobData(pickle.loads(redis_row))

    def as_redis(self):
        return pickle.dumps(self.data)


HUEY_REDIS_DOAJMAINQUEUE = 'huey.redis.doajmainqueue'
HUEY_REDIS_DOAJLONGRUNNING = 'huey.redis.doajlongrunning'
HUEY_REDIS_KEYS = [HUEY_REDIS_DOAJMAINQUEUE, HUEY_REDIS_DOAJLONGRUNNING]


class HueyJobService:

    def create_redis_client(self):
        client = redis.StrictRedis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=0)
        return client

    def find_all_huey_jobs(self, client=None) -> Iterator[HueyJobData]:
        client = client or self.create_redis_client()
        huey_rows = itertools.chain.from_iterable((client.lrange(k, 0, -1)
                                                   for k in HUEY_REDIS_KEYS))
        huey_rows = (HueyJobData.from_redis(r) for r in huey_rows)
        return huey_rows

    def find_queued_huey_jobs(self, client=None) -> Iterator[HueyJobData]:
        client = client or self.create_redis_client()
        return (r for r in self.find_all_huey_jobs(client=client) if not r.is_scheduled)

    def rm_huey_job_from_redis(self, huey_job_data: 'HueyJobData', client=None):
        client = client or self.create_redis_client()
        for key in ['huey.redis.doajmainqueue', 'huey.redis.doajlongrunning']:
            if client.lrem(key, 1, huey_job_data.as_redis()):
                break
