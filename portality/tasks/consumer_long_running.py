# NOTE: this file is designed to be imported by Huey, the background job processor
# It changes the logging configuration. If it's imported anywhere else in the app,
# it will change the logging configuration for the entire app.
import logging

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# import the queues
from portality.tasks.redis_huey import long_running  # noqa

# these are the ones that bind to the long_running queue
from portality.tasks.article_cleanup_sync import scheduled_article_cleanup_sync, article_cleanup_sync  # noqa
from portality.tasks.prune_es_backups import scheduled_prune_es_backups, prune_es_backups  # noqa
from portality.tasks.public_data_dump import scheduled_public_data_dump, public_data_dump  # noqa
from portality.tasks.harvester import scheduled_harvest  # noqa
from portality.tasks.anon_export import scheduled_anon_export, anon_export  # noqa
from portality.tasks.old_data_cleanup import scheduled_old_data_cleanup, execute_old_data_cleanup  # noqa
from portality.tasks.monitor_bgjobs import scheduled_monitor_bgjobs, execute_monitor_bgjobs # noqa
