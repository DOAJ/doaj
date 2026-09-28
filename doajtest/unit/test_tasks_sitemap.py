from doajtest.fixtures import ArticleFixtureFactory, JournalFixtureFactory
from doajtest.helpers import DoajTestCase, StoreLocalPatcher
from doajtest.unit_tester import bgtask_tester
from portality import dao, models
from portality.background import BackgroundApi
from portality.constants import BgjobOutcomeStatus
from portality.core import app
from portality.lib.thread_utils import wait_until
from portality.store import StoreFactory
from portality.tasks import sitemap


class TestSitemap(DoajTestCase):

    def setUp(self):
        super(TestSitemap, self).setUp()
        self.store_local_patcher = StoreLocalPatcher()
        self.store_local_patcher.setUp(self.app_test)
        self.container_id = app.config.get("STORE_CACHE_CONTAINER")
        self.mainStore = StoreFactory.get("cache")

        # Force mappings via a throwaway write, same pattern as DoajTestCase.fix_es_mapping().
        for m in [
            models.Journal(**JournalFixtureFactory.make_journal_source()),
            models.Article(**ArticleFixtureFactory.make_article_source()),
        ]:
            m.save(blocking=True)
            dao.DomainObject.delete(m)

    def tearDown(self):
        super(TestSitemap, self).tearDown()
        self.mainStore.delete_container(self.container_id)
        self.store_local_patcher.tearDown(self.app_test)

    def test_01_sitemap(self):
        user = app.config.get("SYSTEM_USERNAME")
        job = sitemap.SitemapBackgroundTask.prepare(user)
        task = sitemap.SitemapBackgroundTask(job)
        BackgroundApi.execute(task)

        # Fail fast with the real reason (rather than a downstream FileNotFoundError)
        # if the task itself didn't succeed.
        assert job.outcome_status == BgjobOutcomeStatus.Success, job.pretty_audit

        def _sitemap_written():
            try:
                return len(self.mainStore.list(self.container_id)) == 1
            except FileNotFoundError:
                return False

        # The store write can lag slightly behind the (synchronous) task completing,
        # under CI's more constrained/contended resources - poll instead of a fixed sleep.
        wait_until(_sitemap_written, timeout=10,
                  timeout_msg="sitemap file was not written to the store within 10s:\n" + job.pretty_audit)

    def test_prepare__queue_id(self):
        bgtask_tester.test_queue_id_assigned(sitemap.SitemapBackgroundTask)
