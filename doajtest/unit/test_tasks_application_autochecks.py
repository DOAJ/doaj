import time

from doajtest.helpers import DoajTestCase, StoreLocalPatcher
from doajtest.unit_tester import bgtask_tester
from portality.background import BackgroundApi
from portality.core import app
from portality.store import StoreFactory
from portality.tasks import sitemap


class TestApplicationAutochecks(DoajTestCase):

    def setUp(self):
        super(TestApplicationAutochecks, self).setUp()

    def tearDown(self):
        super(TestApplicationAutochecks, self).tearDown()

    def test_01_application_not_found(self):
        user = app.config.get("SYSTEM_USERNAME")
        job = sitemap.SitemapBackgroundTask.prepare(user)
        task = sitemap.SitemapBackgroundTask(job)
        BackgroundApi.execute(task)
        time.sleep(2)
        assert len(self.mainStore.list(self.container_id)) == 1

    def test_prepare__queue_id(self):
        bgtask_tester.test_queue_id_assigned(sitemap.SitemapBackgroundTask)
