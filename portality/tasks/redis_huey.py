from huey import RedisHuey, crontab
from portality.core import app

# every-day background jobs that take a few minutes each (like, bulk deletes and anything else requested by the user)
# DEPRECATED
main_queue = RedisHuey('doaj_main_queue',
                       host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'],
                       immediate=app.config.get("HUEY_IMMEDIATE", False))

# jobs that might take a long time, like the harvester or the anon export, which can run for several hours
# DEPRECATED
long_running = RedisHuey('doaj_long_running',
                         host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'],
                         immediate=app.config.get("HUEY_IMMEDIATE", False))


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

"""
we put everything we want to be responsive onto the main_queue, 
and anything that would disrupt the main_queue by taking too 
long goes on long_running
"""


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


def run_bgjobs_immediately():
    main_queue.always_eager = True
    long_running.always_eager = True
    main_queue.immediate = True
    long_running.immediate = True
