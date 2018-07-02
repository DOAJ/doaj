"""
This script allows you to manually (and synchronously) execute the article duplicate reporting task
"""
import logging
import sys

from portality.background import BackgroundApi
from portality.core import app
from portality.lib import dates
from portality.tasks import article_duplicate_report

if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-o", "--out",
                        help="Output directory in which article duplicate reports should be saved (will be created if it doesn't exist)",
                        default="article_duplicates_" + dates.today())
    parser.add_argument("-e", "--email",
                        help="Send zip archived reports to email addresses configured via REPORTS_EMAIL_TO in settings",
                        action='store_true')
    parser.add_argument('-v', '--verbose',
                        help='Print the csv to console as we build it.',
                        action='store_true')
    parser.add_argument('-vv', '--very_verbose',
                        help='Print extra debug messages - iteration number and article ID',
                        action='store_true')
    args = parser.parse_args()

    # Streamline the logging format if we are doing verbose output.
    if args.verbose or args.very_verbose:
        app.logger.handlers = []
        formatter = logging.Formatter('%(message)s')
        lggr = logging.StreamHandler(sys.stderr)
        lggr.setFormatter(formatter)
        app.logger.addHandler(lggr)

    if args.verbose:
        app.logger.setLevel(logging.INFO)
    if args.very_verbose:
        app.logger.setLevel(logging.DEBUG)

    user = app.config.get("SYSTEM_USERNAME")
    job = article_duplicate_report.ArticleDuplicateReportBackgroundTask.prepare(user, outdir=args.out, email=args.email)
    task = article_duplicate_report.ArticleDuplicateReportBackgroundTask(job)
    BackgroundApi.execute(task)
