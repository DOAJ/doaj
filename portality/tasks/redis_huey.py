from huey import RedisHuey
from portality.core import app

main_queue = RedisHuey('doaj', host=app.config['HUEY_REDIS_HOST'], port=app.config['HUEY_REDIS_PORT'])
