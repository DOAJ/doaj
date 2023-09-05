from huey import RedisHuey, crontab
from portality.core import app

# every-day background jobs that take a few minutes each (like, bulk deletes and anything else requested by the user)
main_queue = RedisHuey('doaj_main_queue', host=app.config['HUEY_REDIS_HOST'], port=app.config['HUEY_REDIS_PORT'], always_eager=app.config.get("HUEY_EAGER", False))

# jobs that might take a long time, like the harvester or the anon export, which can run for several hours
long_running = RedisHuey('doaj_long_running', host=app.config['HUEY_REDIS_HOST'], port=app.config['HUEY_REDIS_PORT'], always_eager=app.config.get("HUEY_EAGER", False))

"""
we put everything we want to be responsive onto the main_queue, 
and anything that would disrupt the main_queue by taking too 
long goes on long_running
"""


def schedule(action):
    cfg = app.config.get("HUEY_SCHEDULE", {})
    action_cfg = cfg.get(action)
    if action_cfg is None:
        raise RuntimeError("No configuration for scheduled action '{x}'.  Define this in HUEY_SCHEDULE first then try again.".format(x=action))

    return crontab(**action_cfg)


def configure(action):
    cfg = app.config.get("HUEY_TASKS", {})
    action_cfg = cfg.get(action)
    if action_cfg is None:
        raise RuntimeError("No task configuration for action '{x}'.  Define this in HUEY_TASKS first then try again.".format(x=action))
    return action_cfg

