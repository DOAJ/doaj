# NOTE: this file is designed to be imported by Huey, the background job processor
# It changes the logging configuration. If it's imported anywhere else in the app,
# it will change the logging configuration for the entire app.
import logging
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

from portality.tasks.redis_huey import main_queue

from portality.tasks.reporting import scheduled_reports, run_reports
from portality.tasks.journal_in_out_doaj import set_in_doaj
from portality.tasks.sitemap import scheduled_sitemap, generate_sitemap
from portality.tasks.journal_bulk_edit import journal_bulk_edit
from portality.tasks.suggestion_bulk_edit import suggestion_bulk_edit
from portality.tasks.ingestarticles import ingest_articles
from portality.tasks.journal_csv import scheduled_journal_csv, journal_csv
#from portality.tasks.article_cleanup_sync import scheduled_article_cleanup_sync, article_cleanup_sync
