from portality.tasks.redis_huey import main_queue

from portality.tasks.reporting import scheduled_reports, run_reports
from portality.tasks.journal_in_out_doaj import set_in_doaj
from portality.tasks.sitemap import scheduled_sitemap, generate_sitemap