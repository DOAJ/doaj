from huey import RedisHuey, crontab
from portality.core import app

# short jobs to be run on demand from within the application
events_queue = RedisHuey('doaj_events_queue',
                       host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'],
                       always_eager=app.config.get("HUEY_EAGER", False))

# scheduled jobs that can run for several hours each
scheduled_long_queue = RedisHuey('doaj_scheduled_long_queue',
                         host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'],
                         always_eager=app.config.get("HUEY_EAGER", False))

# scheduled jobs that will typically run within a few minutes
scheduled_short_queue = RedisHuey('doaj_scheduled_short_queue',
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
