"""
use this script if you want to manually (and synchronously) execute the reporting task
"""
from portality.background import BackgroundApi
from portality.core import app
from portality.lib import dates
from portality.tasks import reporting

if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-f", "--from_date",
                        help="Start date for reporting period (YYYY-MM-DDTHH:MM:SSZ)",
                        default="1970-01-01T00:00:00Z")
    parser.add_argument("-t", "--to_date",
                        help="End date for reporting period (YYYY-MM-DDTHH:MM:SSZ)",
                        default=dates.now())
    parser.add_argument("-o", "--out",
                        help="Output directory into which reports should be made (will be created if it doesn't exist)",
                        default="report_" + dates.today())
    parser.add_argument("-e", "--email",
                        help="Send zip archived reports to email addresses configured via REPORTS_EMAIL_TO in settings",
                        action='store_true')
    args = parser.parse_args()

    user = app.config.get("SYSTEM_USERNAME")
    job = reporting.ReportingBackgroundTask.prepare(user, from_date=args.from_date, to_date=args.to_date, outdir=args.out, email=args.email)
    task = reporting.ReportingBackgroundTask(job)
    BackgroundApi.execute(task)
