# NOTE: this file is designed to be imported by Huey, the background job processor
# It changes the logging configuration. If it's imported anywhere else in the app,
# it will change the logging configuration for the entire app.
import logging
from portality.core import app

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# import the queues
from portality.tasks.redis_huey import events_queue  # noqa

# now import the tasks that will bind to those queues

from portality.tasks.article_bulk_create import article_bulk_create  # noqa
from portality.tasks.article_bulk_delete import article_bulk_delete  # noqa
from portality.tasks.ingestarticles import ingest_articles  # noqa
from portality.tasks.journal_bulk_delete import journal_bulk_delete  # noqa
from portality.tasks.journal_bulk_edit import journal_bulk_edit  # noqa
from portality.tasks.preservation import preserve  # noqa
from portality.tasks.journal_in_out_doaj import set_in_doaj  # noqa
from portality.tasks.suggestion_bulk_edit import suggestion_bulk_edit  # noqa
from portality.tasks.admin_reports import admin_reports  # noqa

# Conditionally enable new application autochecking
if app.config.get("AUTOCHECK_INCOMING", False):
    from portality.tasks.application_autochecks import application_autochecks
