"""
use this script if you want to manually (and synchronously) execute the article duplicate reporting task
"""
from portality.background import BackgroundApi
from portality.core import app
from portality.lib import dates
from portality.tasks import article_duplicates_report_remove

if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-o", "--out",
                        help="Output directory into which article duplicate reports should be made (will be created if it doesn't exist)",
                        default="article_duplicates_" + dates.today())
    parser.add_argument("-e", "--email",
                        help="Send zip archived reports to email addresses configured via REPORTS_EMAIL_TO in settings",
                        action='store_true')
    args = parser.parse_args()

    user = app.config.get("SYSTEM_USERNAME")
    job = article_duplicates_report_remove.ArticleDuplicateReportBackgroundTask.prepare(user, outdir=args.out, email=args.email)
    task = article_duplicates_report_remove.ArticleDuplicateReportBackgroundTask(job)
    BackgroundApi.execute(task)
