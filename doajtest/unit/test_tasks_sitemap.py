import time

from doajtest.helpers import DoajTestCase, StoreLocalPatcher
from doajtest.unit_tester import bgtask_tester
from portality.background import BackgroundApi
from portality.core import app
from portality.store import StoreFactory
from portality.tasks import sitemap


class TestSitemap(DoajTestCase):

    def setUp(self):
        super(TestSitemap, self).setUp()
        self.store_local_patcher = StoreLocalPatcher()
        self.store_local_patcher.setUp(self.app_test)
        self.container_id = app.config.get("STORE_CACHE_CONTAINER")
        self.mainStore = StoreFactory.get("cache")

    def tearDown(self):
        super(TestSitemap, self).tearDown()
        self.mainStore.delete_container(self.container_id)
        self.store_local_patcher.tearDown(self.app_test)

    def test_01_sitemap(self):
        user = app.config.get("SYSTEM_USERNAME")
        job = sitemap.SitemapBackgroundTask.prepare(user)
        task = sitemap.SitemapBackgroundTask(job)
        BackgroundApi.execute(task)
        time.sleep(2)
        assert len(self.mainStore.list(self.container_id)) == 1

    def test_prepare__queue_id(self):
        bgtask_tester.test_queue_id_assigned(sitemap.SitemapBackgroundTask)
