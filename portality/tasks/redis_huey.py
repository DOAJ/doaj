from huey import RedisHuey, crontab
from portality.core import app
from portality.lib import dates


class TimestampedRedisHuey(RedisHuey):
    """ Stamps task failures stored in the result store, so they can be matched to e.g. index downtime """
    def build_error_result(self, task, exception):
        result = super().build_error_result(task, exception)
        result['timestamp'] = dates.now_str_with_microseconds()
        return result


# short jobs to be run on demand from within the application
events_queue = TimestampedRedisHuey('doaj_events_queue',
                       host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'],
                       always_eager=app.config.get("HUEY_EAGER", False))

# scheduled jobs that can run for several hours each
scheduled_long_queue = TimestampedRedisHuey('doaj_scheduled_long_queue',
                         host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'],
                         always_eager=app.config.get("HUEY_EAGER", False))

# scheduled jobs that will typically run within a few minutes
scheduled_short_queue = TimestampedRedisHuey('doaj_scheduled_short_queue',
                         host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'],
                         always_eager=app.config.get("HUEY_EAGER", False))


def schedule(action):
    cfg = app.config.get("HUEY_SCHEDULE", {})
    action_cfg = cfg.get(action)
    if action_cfg is None:
        raise RuntimeError(
            "No configuration for scheduled action '{x}'.  Define this in HUEY_SCHEDULE first then try again."
            .format(x=action))

    return crontab(**action_cfg)


def configure(action):
    cfg = app.config.get("HUEY_TASKS", {})
    action_cfg = cfg.get(action)
    if action_cfg is None:
        raise RuntimeError(
            "No task configuration for action '{x}'.  Define this in HUEY_TASKS first then try again."
            .format(x=action))
    return action_cfg
