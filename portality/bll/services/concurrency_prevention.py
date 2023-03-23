

class DuplicationPreventionService:
    def __init__(self):
        self.rc = redis.Redis(host=app.config.get("HUEY_REDIS_HOST"), port=app.config.get("HUEY_REDIS_PORT"))

    def check_concurrency(self, journal, id):
        aid = rc.get(journal)
        if aid is not None and aid != id:
            raise ConcurrentUpdateRequestException()
        rc.set(journal, id, ex=10)