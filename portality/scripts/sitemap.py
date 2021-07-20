"""
use this script if you want to manually (and synchronously) execute the sitemap task
~~Sitemap:Script->Sitemap:Feature~~
"""
from portality.tasks import sitemap
from portality.core import app
from portality.background import BackgroundApi

if __name__ == "__main__":
    user = app.config.get("SYSTEM_USERNAME")
    # ~~->Sitemap:BackgroundTask~~
    job = sitemap.SitemapBackgroundTask.prepare(user)
    task = sitemap.SitemapBackgroundTask(job)
    BackgroundApi.execute(task)
    print(job.pretty_audit)


