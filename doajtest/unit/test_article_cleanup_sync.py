from doajtest.helpers import DoajTestCase
from doajtest import fixtures

from portality import background, models
from portality.tasks import article_cleanup_sync

from datetime import datetime
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
        j.save(blocking=True)

        # the identifiers to allow us to connect articles to the journal
        eissn = j.bibjson().get_identifiers(j.bibjson().E_ISSN)[0]
        pissn = j.bibjson().get_identifiers(j.bibjson().P_ISSN)[0]

        # an article source which is already synchronised with its journal
        source2 = fixtures.ArticleFixtureFactory.make_article_source(eissn=eissn, pissn=pissn, with_journal_info=False, with_id=False)
        a1 = models.Article(**source2)
        a1.add_journal_metadata(j)
        a1.save(blocking=True)

        # do not add any journal metadata
        source3 = fixtures.ArticleFixtureFactory.make_article_source(eissn=eissn, pissn=pissn, with_journal_info=False, with_id=False)
        a2 = models.Article(**source3)
        a2.save(blocking=True)

        # a record which is not connected to an existing journal
        source4 = fixtures.ArticleFixtureFactory.make_article_source(eissn="xxxx-xxxx", pissn="xxxx-xxxx", with_journal_info=False, with_id=False)
        a3 = models.Article(**source4)
        assert a3.get_journal() is None
        a3.save(blocking=True)

        # We should have one journal and three articles
        assert models.Journal.count() == 1
        assert models.Article.count() == 3

        # run the sync/cleanup job
        job = article_cleanup_sync.ArticleCleanupSyncBackgroundTask.prepare("testuser", write=True)
        task = article_cleanup_sync.ArticleCleanupSyncBackgroundTask(job)
        background.BackgroundApi.execute(task)

        time.sleep(2)

        # We now have one journal and two articles
        assert models.Journal.count() == 1
        assert models.Article.count() == 2

        # retrieve any updated records
        a1u = models.Article.pull(a1.id)
        a2u = models.Article.pull(a2.id)
        a3u = models.Article.pull(a3.id)

        # we expect this one not to have changed
        assert a1u.bibjson().data.get("journal") == a1.bibjson().data.get("journal")
        assert a1u.last_updated == a1.last_updated, (a1u.last_updated, a1.last_updated)

        # we expect this one to have had its journal info updated
        assert a2u.bibjson().data.get("journal") is not None

        # this one should have been deleted
        assert a3u is None

    def test_03_prepall(self):
        # a journal from which we will sync metadata
        source = fixtures.JournalFixtureFactory.make_journal_source(in_doaj=True)
        j = models.Journal(**source)
        j.save()

        # the identifiers to allow us to connect articles to the journal
        eissn = j.bibjson().get_identifiers(j.bibjson().E_ISSN)[0]
        pissn = j.bibjson().get_identifiers(j.bibjson().P_ISSN)[0]

        # an article source which is already synchronised with its journal
        source2 = fixtures.ArticleFixtureFactory.make_article_source(eissn=eissn, pissn=pissn, with_journal_info=False,
                                                                            with_id=False)
        a1 = models.Article(**source2)
        a1.add_journal_metadata(j)
        a1.save()

        # do not add any journal metadata
        source3 = fixtures.ArticleFixtureFactory.make_article_source(eissn=eissn, pissn=pissn, with_journal_info=False,
                                                                            with_id=False)
        a2 = models.Article(**source3)
        a2.save()

        # Add an article which is not connected to an existing journal, so will be cleaned up
        source4 = fixtures.ArticleFixtureFactory.make_article_source(eissn="xxxx-xxxx", pissn="xxxx-xxxx",
                                                                            with_journal_info=False, with_id=False)
        a3 = models.Article(**source4)
        a3.save(blocking=True)

        time.sleep(1)

        # run the sync/cleanup job
        job = article_cleanup_sync.ArticleCleanupSyncBackgroundTask.prepare("testuser", write=True, prepall=True)
        task = article_cleanup_sync.ArticleCleanupSyncBackgroundTask(job)
        background.BackgroundApi.execute(task)

        time.sleep(2)

        # retrieve any updated records
        a1u = models.Article.pull(a1.id)
        a2u = models.Article.pull(a2.id)
        a3u = models.Article.pull(a3.id)

        # we expect this one not to have changed, but have been prepared anyway
        assert a1u.bibjson().data.get("journal") == a1.bibjson().data.get("journal")
        assert datetime.strptime(a1u.last_updated, "%Y-%m-%dT%H:%M:%SZ") > datetime.strptime(a1.last_updated, "%Y-%m-%dT%H:%M:%SZ")

        # we expect this one to have had its journal info updated
        assert a2u.bibjson().data.get("journal") is not None
        assert datetime.strptime(a2u.last_updated, "%Y-%m-%dT%H:%M:%SZ") > datetime.strptime(a2.last_updated, "%Y-%m-%dT%H:%M:%SZ")

        # this one should have been deleted
        assert a3u is None

    def test_04_odd_sync_situations(self):
        # If articles contain ISSNS for >1 distinct journals, we should choose the 'best'

        [jk_s, l_s, m_s] = fixtures.JournalFixtureFactory.make_many_journal_sources(3, in_doaj=False)

        # a journal from which we will sync metadata
        jk_s['admin']['in_doaj'] = True
        j = models.Journal(**jk_s)
        j.save()

        # another journal that looks suspiciously like the first, more recently updated
        copied_journal_title = "This is a duplicate journal"
        jk_s['bibjson']['title'] = copied_journal_title
        k = models.Journal(**jk_s)
        k.set_last_manual_update()
        k.save()

        # a third journal, different to the first two and it's not in the DOAJ.
        bad_journal_title = "This is an undesirable journal because it is not in DOAJ"
        l_s['bibjson']['title'] = bad_journal_title
        l = models.Journal(**l_s)
        l.save()

        # yet another journal, distinct but in the DOAJ
        good_journal_title = "This is a good journal because it is in DOAJ"
        m_s['bibjson']['title'] = good_journal_title
        m_s['admin']['in_doaj'] = True
        m = models.Journal(**m_s)
        m.save()

        # the identifiers to allow us to connect articles to the journal
        jk_eissn = j.bibjson().get_identifiers(j.bibjson().E_ISSN)[0]
        jk_pissn = j.bibjson().get_identifiers(j.bibjson().P_ISSN)[0]
        l_eissn =l.bibjson().get_identifiers(l.bibjson().E_ISSN)[0]
        l_pissn = l.bibjson().get_identifiers(l.bibjson().P_ISSN)[0]
        m_pissn = m.bibjson().get_identifiers(m.bibjson().P_ISSN)[0]

        # an article source which is already synchronised with both journals j and k
        source = fixtures.ArticleFixtureFactory.make_article_source(eissn=jk_eissn, pissn=jk_pissn, with_journal_info=False,
                                                                           with_id=False)
        a1 = models.Article(**source)
        a1.add_journal_metadata(j)
        a1.save()

        # an article without metadata, but whose ISSNs match both j and k
        source2 = fixtures.ArticleFixtureFactory.make_article_source(eissn=jk_eissn, pissn=jk_pissn, with_journal_info=False,
                                                                            with_id=False)
        a2 = models.Article(**source2)
        a2.save()

        # an article that matches two different journal ISSNs
        source3 = fixtures.ArticleFixtureFactory.make_article_source(eissn=l_eissn, pissn=m_pissn,
                                                                            with_journal_info=False,
                                                                            with_id=False)
        a3 = models.Article(**source3)
        a3.save()

        # an article without metadata, but whose ISSNs match both j and k
        source4 = fixtures.ArticleFixtureFactory.make_article_source(eissn=l_eissn, pissn=l_pissn,
                                                                            with_journal_info=False,
                                                                            with_id=False)
        a4 = models.Article(**source4)
        a4.save(blocking=True)

        # run the sync/cleanup job
        job = article_cleanup_sync.ArticleCleanupSyncBackgroundTask.prepare("testuser", write=True)
        task = article_cleanup_sync.ArticleCleanupSyncBackgroundTask(job)
        background.BackgroundApi.execute(task)

        time.sleep(2)

        # retrieve any updated records
        a1u = models.Article.pull(a1.id)
        a2u = models.Article.pull(a2.id)
        a3u = models.Article.pull(a3.id)
        a4u = models.Article.pull(a4.id)

        # a1 and a2 should have synced with journal k, the more recent one
        assert a1u.bibjson().journal_title == copied_journal_title
        assert a2u.bibjson().journal_title == copied_journal_title

        # a3 should have synced with the journal that was in_doaj
        assert a3u.bibjson().journal_title == good_journal_title

        # a4 should have the journal info for journal l
        assert a4u.bibjson().journal_title == bad_journal_title

    def test_05_best_journal(self):
        j1 = models.Journal()
        j1.set_in_doaj(True)
        j1.set_last_manual_update("2001-01-01T00:00:00Z")
        j1.save()

        j2 = models.Journal()
        j2.set_in_doaj(True)
        j2.save()

        j3 = models.Journal()
        j3.set_in_doaj(False)
        j3.set_last_manual_update("2002-01-01T00:00:00Z")
        j3.save()

        j4 = models.Journal()
        j4.set_in_doaj(False)
        j4.save(blocking=True)

        job = article_cleanup_sync.ArticleCleanupSyncBackgroundTask.prepare("testuser")
        task = article_cleanup_sync.ArticleCleanupSyncBackgroundTask(job)

        # the degenerate case, when there's only one journal
        best = task._get_best_journal([j1])
        assert best.id == j1.id

        # should return in doaj over not in doaj
        best = task._get_best_journal([j1, j3])
        assert best.id == j1.id

        # should return manually updated over not manually updated
        best = task._get_best_journal([j1, j2])
        assert best.id == j1.id

        best = task._get_best_journal([j3, j4])
        assert best.id == j3.id
