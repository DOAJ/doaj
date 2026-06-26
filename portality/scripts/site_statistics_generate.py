"""
use this script if you want to manually generate the site statistics
"""
from portality.core import app
from portality.background import BackgroundApi
from portality.tasks.site_statistics import SiteStatisticsBackgroundTask

if __name__ == "__main__":
    user = app.config.get("SYSTEM_USERNAME")
    job = SiteStatisticsBackgroundTask.prepare(user)
    task = SiteStatisticsBackgroundTask(job)
    BackgroundApi.execute(task)
    print(job.pretty_audit)


