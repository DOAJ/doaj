from doajtest.helpers import DoajTestCase
from doajtest import fixtures

from portality import background, models
from portality.tasks import article_cleanup_sync

import time


class TestArticleCleanupSync(DoajTestCase):

    def setUp(self):
        super(TestArticleCleanupSync, self).setUp()

    def tearDown(self):
        super(TestArticleCleanupSync, self).tearDown()

    def test_01_prepare(self):
        job = article_cleanup_sync.ArticleCleanupSyncBackgroundTask.prepare("testuser")
        assert job.params.get("article_cleanup_sync__write") is True
        assert job.params.get("article_cleanup_sync__prepall") is False

        job = article_cleanup_sync.ArticleCleanupSyncBackgroundTask.prepare("testuser", prepall=True, write=True)
        assert job.params.get("article_cleanup_sync__write") is True
        assert job.params.get("article_cleanup_sync__prepall") is True
        assert len(job.audit) == 1

        with self.assertRaises(background.BackgroundException):
            job = article_cleanup_sync.ArticleCleanupSyncBackgroundTask.prepare("testuser", prepall=True, write=False)

        job = article_cleanup_sync.ArticleCleanupSyncBackgroundTask.prepare("testuser", prepall=False, write=False)
        assert job.params.get("article_cleanup_sync__write") is False
        assert job.params.get("article_cleanup_sync__prepall") is False

    def test_02_write(self):
        # a journal from which we will sync metadata
        source = fixtures.JournalFixtureFactory.make_journal_source(in_doaj=True)
        j = models.Journal(**source)
        j.save()

        # the identifiers to allow us to connect articles to the journal
        eissn = j.bibjson().get_identifiers(j.bibjson().E_ISSN)[0]
        pissn = j.bibjson().get_identifiers(j.bibjson().P_ISSN)[0]

        # an article source which is already synchronised with its journal
        source2 = fixtures.ArticleFixtureFactory.make_article_source(eissn=eissn, pissn=pissn, with_journal_info=False, with_id=False)
        a1 = models.Article(**source2)
        a1.add_journal_metadata(j)
        a1.save()

        # do not add any journal metadata
        source3 = fixtures.ArticleFixtureFactory.make_article_source(eissn=eissn, pissn=pissn, with_journal_info=False, with_id=False)
        a2 = models.Article(**source3)
        a2.save()

        # a record which is not connected to an existing journal
        source4 = fixtures.ArticleFixtureFactory.make_article_source(eissn="xxxx-xxxx", pissn="xxxx-xxxx", with_journal_info=False, with_id=False)
        a3 = models.Article(**source4)
        a3.save(blocking=True)

        # run the sync/cleanup job
        job = article_cleanup_sync.ArticleCleanupSyncBackgroundTask.prepare("testuser")
        article_cleanup_sync.ArticleCleanupSyncBackgroundTask.submit(job)

        time.sleep(2)

        # retrieve any updated records
        a1u = models.Article.pull(a1.id)
        a2u = models.Article.pull(a2.id)
        a3u = models.Article.pull(a3.id)

        # we expect this one not to have changed
        assert a1u.bibjson().data.get("journal") == a1.bibjson().data.get("journal")

        # we expect this one to have had its journal info updated
        assert a2u.bibjson().data.get("journal") is not None

        # this one should have been deleted
        assert a3u is None
