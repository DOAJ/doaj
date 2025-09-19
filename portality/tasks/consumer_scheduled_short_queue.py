# NOTE: this file is designed to be imported by Huey, the background job processor
# It changes the logging configuration. If it's imported anywhere else in the app,
# it will change the logging configuration for the entire app.
import logging
from portality.core import app

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# import the queues
from portality.tasks.redis_huey import scheduled_short_queue  # noqa

# now import the tasks that will bind to those queues
from portality.tasks.async_workflow_notifications import async_workflow_notifications  # noqa
from portality.tasks.check_latest_es_backup import scheduled_check_latest_es_backup, check_latest_es_backup  # noqa
from portality.tasks.datalog_journal_added_update import scheduled_datalog_journal_added_update, datalog_journal_added_update  # noqa
from portality.tasks.find_discontinued_soon import scheduled_find_discontinued_soon, find_discontinued_soon  # noqa
from portality.tasks.journal_csv import scheduled_journal_csv, journal_csv  # noqa
from portality.tasks.monitor_bgjobs import scheduled_monitor_bgjobs, monitor_bgjobs  # noqa
from portality.tasks.old_data_cleanup import scheduled_old_data_cleanup, old_data_cleanup  # noqa
from portality.tasks.prune_es_backups import scheduled_prune_es_backups, prune_es_backups  # noqa
from portality.tasks.read_news import scheduled_read_news, read_news  # noqa
from portality.tasks.reporting import scheduled_reports, run_reports  # noqa
from portality.tasks.request_es_backup import scheduled_request_es_backup, request_es_backup  # noqa
from portality.tasks.auto_assign_editor_group_data import scheduled_auto_assign_editor_group_data, auto_assign_editor_group_data
