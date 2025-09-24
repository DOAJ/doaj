from portality.core import app
from portality.lib import dates
import redis
import json
import hashlib

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

    # Passwordless login resend backoff tracking
    def record_pwless_resend(self, email: str, now: int | None = None):
        """
        Check and record a passwordless login code resend for the given email with exponential backoff.

        Returns a tuple: (allowed: bool, wait_remaining: int, current_interval: int)
        - allowed: whether a resend is permitted right now
        - wait_remaining: seconds to wait until next allowed resend (0 if allowed)
        - current_interval: the interval applied/returned for UI cooldown
        """
        if not email:
            return False, 60, 60

        email_key = hashlib.sha1(email.lower().encode("utf-8")).hexdigest()
        key = f"pwless_resend:{email_key}"
        now = now or dates.now_in_sec()

        min_interval = int(app.config.get("PWLESS_RESEND_MIN_INTERVAL", 60))
        max_interval = int(app.config.get("PWLESS_RESEND_MAX_INTERVAL", 86400))  # 24 hours
        factor = float(app.config.get("PWLESS_RESEND_BACKOFF_FACTOR", 2.0))
        ttl = int(app.config.get("PWLESS_RESEND_RECORD_TTL", max_interval * 2))

        raw = self.rs.get(key)
        record = json.loads(raw.decode('utf-8')) if raw else None

        if record:
            next_allowed_at = int(record.get("next_allowed_at", 0))
            count = int(record.get("count", 0))
            current_interval = int(record.get("current_interval", min_interval))
            if now < next_allowed_at:
                return False, next_allowed_at - now, current_interval
            # allowed: back off interval for next time
            new_interval = int(min(max_interval, max(min_interval, current_interval * factor)))
            new_count = count + 1
        else:
            new_interval = min_interval
            new_count = 1

        next_allowed_at = now + new_interval
        new_record = {
            "last_request": now,
            "count": new_count,
            "current_interval": new_interval,
            "next_allowed_at": next_allowed_at,
        }
        self.rs.set(key, json.dumps(new_record), ex=ttl)
        return True, 0, new_interval
