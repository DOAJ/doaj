"""
Manually execute the reapplication reporting task
"""
from portality.background import BackgroundApi
from portality.core import app
from portality.lib import dates
from portality.tasks import reapplication_reporting

if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-o", "--out",
                        help="Output directory into which reports should be made (will be created if it doesn't exist)",
                        default="reapplication_report_" + dates.today())
    parser.add_argument("-e", "--email",
                        help="Send zip archived reports to email addresses configured via REPORTS_EMAIL_TO in settings",
                        action='store_true')
    args = parser.parse_args()

    user = app.config.get("SYSTEM_USERNAME")
    job = reapplication_reporting.ReportingBackgroundTask.prepare(user, outdir=args.out, email=args.email)
    task = reapplication_reporting.ReportingBackgroundTask(job)
    BackgroundApi.execute(task)
