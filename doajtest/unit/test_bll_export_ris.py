# -*- coding: UTF-8 -*-
import time

from doajtest.fixtures import ArticleFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.lib import dates
from portality.lib.thread_utils import wait_until
from portality import models
from portality.bll import DOAJ

class TestBLLExportRIS(DoajTestCase):

    def setUp(self):
        super(TestBLLExportRIS, self).setUp()
        self.svc = DOAJ.exportService()

    def tearDown(self):
        super(TestBLLExportRIS, self).tearDown()

    def test_01_individual_record(self):
        a = ArticleFixtureFactory.make_article_source()
        article = models.Article(**a)
        article.pre_save_prep()

        ris = self.svc.ris(article, save=True)
        wait_until(lambda: models.RISExport.pull(ris.id) is not None, timeout=5, sleep_time=0.5)

        ris2 = models.RISExport.pull(ris.id)
        assert ris2.ris_raw == ris.ris_raw

    def test_02_delete_ris(self):
        a = ArticleFixtureFactory.make_article_source()
        article = models.Article(**a)
        article.pre_save_prep()

        ris = self.svc.ris(article, save=True)
        wait_until(lambda: models.RISExport.pull(ris.id) is not None, timeout=5, sleep_time=0.5)

        ris2 = models.RISExport.pull(ris.id)
        assert ris2 is not None

        self.svc.remove_ris(ris2.id)
        ris3 = models.RISExport.pull(ris2.id)
        assert ris3 is None

    def test_03_stale(self):
        a = ArticleFixtureFactory.make_article_source()
        article = models.Article(**a)
        article.pre_save_prep()

        # There's no RIS so it's stale by definition
        stale = self.svc.has_stale_ris(article)
        assert stale is True

        ris = self.svc.ris(article, save=True)
        wait_until(lambda: models.RISExport.pull(ris.id) is not None, timeout=5, sleep_time=0.5)

        # The RIS is current so is not stale
        stale = self.svc.has_stale_ris(article)
        assert stale is False

        article.data["last_updated"] = dates.format(dates.seconds_after_now(100))

        # The RIS is before the last updated date
        stale = self.svc.has_stale_ris(article)
        assert stale is True

    def test_04_bulk(self):
        sources = ArticleFixtureFactory.make_many_article_sources(10, in_doaj=True)
        articles = [models.Article(**x) for x in sources]
        for article in articles:
            article.save()
        models.Article.blockall([(a.id, a.last_updated) for a in articles])

        export = articles[:8]
        existing = []
        for article in export:
            existing.append(self.svc.ris(article))
        models.RISExport.blockall([(r.id, r.last_updated) for r in existing])

        time.sleep(1)

        stale = export[:6]
        stale_unchanged = stale[:3]
        stale_changed = stale[3:]
        for article in stale_unchanged:
            article.save()
        for article in stale_changed:
            article.bibjson().title = "New title that has changed"
            article.save()
        models.Article.blockall([(a.id, a.last_updated) for a in stale])

        report = self.svc.bulk_generate_ris(force_update=False)
        processed, loaded = report.counts()
        assert processed == 10
        assert loaded == 5 # 2 missing, 3 stale and changed

        wait_until(lambda : models.RISExport.count() == 10)

        report = self.svc.bulk_generate_ris(force_update=True)
        processed, loaded = report.counts()
        assert processed == 10
        assert loaded == 10 # everything reloaded






