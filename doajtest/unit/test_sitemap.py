from doajtest.helpers import DoajTestCase
from portality.core import app
from portality.tasks import sitemap
from portality.background import BackgroundApi
import os, shutil, time
from portality.lib import paths

class TestSitemap(DoajTestCase):

    def setUp(self):
        super(TestSitemap, self).setUp()
        self.cache_dir = app.config.get("CACHE_DIR")
        self.tmp_dir = paths.rel2abs(__file__, "tmp-cache")
        app.config["CACHE_DIR"] = self.tmp_dir

    def tearDown(self):
        super(TestSitemap, self).tearDown()
        app.config["CACHE_DIR"] = self.cache_dir
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_01_sitemap(self):
        user = app.config.get("SYSTEM_USERNAME")
        job = sitemap.SitemapBackgroundTask.prepare(user)
        task = sitemap.SitemapBackgroundTask(job)
        BackgroundApi.execute(task)
        time.sleep(1)
        assert len(os.listdir(os.path.join(self.tmp_dir, "sitemap"))) == 1