from doajtest.helpers import DoajTestCase
from portality.core import app
from portality.tasks import sitemap
from portality.background import BackgroundApi
import os, shutil, time
from portality.lib import paths
from portality.store import StoreFactory


class TestSitemap(DoajTestCase):
    store_impl = None

    @classmethod
    def setUpClass(cls) -> None:
        super(TestSitemap, cls).setUpClass()
        cls.store_impl = app.config["STORE_IMPL"]
        app.config["STORE_IMPL"] = "portality.store.StoreLocal"

    @classmethod
    def tearDownClass(cls) -> None:
        super(TestSitemap, cls).tearDownClass()
        app.config["STORE_IMPL"] = cls.store_impl

    def setUp(self):
        super(TestSitemap, self).setUp()
        self.container_id = app.config.get("STORE_CACHE_CONTAINER")
        self.mainStore = StoreFactory.get("cache")

    def tearDown(self):
        super(TestSitemap, self).tearDown()
        self.mainStore.delete_container(self.container_id)

    def test_01_sitemap(self):
        user = app.config.get("SYSTEM_USERNAME")
        job = sitemap.SitemapBackgroundTask.prepare(user)
        task = sitemap.SitemapBackgroundTask(job)
        BackgroundApi.execute(task)
        time.sleep(1.5)
        assert len(self.mainStore.list(self.container_id)) == 1