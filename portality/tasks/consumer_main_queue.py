# NOTE: this file is designed to be imported by Huey, the background job processor
# It changes the logging configuration. If it's imported anywhere else in the app,
# it will change the logging configuration for the entire app.
import logging

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# import the queues
from portality.tasks.redis_huey import main_queue  # noqa

# now import the tasks that will bind to those queues

# these are the ones which bind to the main_queue
from portality.tasks.reporting import scheduled_reports, run_reports  # noqa
from portality.tasks.journal_in_out_doaj import set_in_doaj  # noqa
from portality.tasks.sitemap import scheduled_sitemap, generate_sitemap  # noqa
from portality.tasks.journal_bulk_edit import journal_bulk_edit  # noqa
from portality.tasks.suggestion_bulk_edit import suggestion_bulk_edit  # noqa
from portality.tasks.ingestarticles import ingest_articles  # noqa
from portality.tasks.preservation import preserve  # noqa
from portality.tasks.journal_csv import scheduled_journal_csv, journal_csv  # noqa
from portality.tasks.read_news import scheduled_read_news, read_news  # noqa
from portality.tasks.journal_bulk_delete import journal_bulk_delete  # noqa
from portality.tasks.article_bulk_delete import article_bulk_delete  # noqa
from portality.tasks.async_workflow_notifications import async_workflow_notifications  # noqa
from portality.tasks.check_latest_es_backup import scheduled_check_latest_es_backup, check_latest_es_backup  # noqa
from portality.tasks.request_es_backup import scheduled_request_es_backup, request_es_backup  # noqa
from portality.tasks.find_discontinued_soon import scheduled_find_discontinued_soon, find_discontinued_soon  # noqa
