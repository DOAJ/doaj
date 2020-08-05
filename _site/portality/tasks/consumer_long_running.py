# NOTE: this file is designed to be imported by Huey, the background job processor
# It changes the logging configuration. If it's imported anywhere else in the app,
# it will change the logging configuration for the entire app.
import logging
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# import the queues
from portality.tasks.redis_huey import long_running

# these are the ones that bind to the long_running queue
from portality.tasks.article_cleanup_sync import scheduled_article_cleanup_sync, article_cleanup_sync
from portality.tasks.prune_es_backups import scheduled_prune_es_backups, prune_es_backups
from portality.tasks.public_data_dump import scheduled_public_data_dump, public_data_dump
