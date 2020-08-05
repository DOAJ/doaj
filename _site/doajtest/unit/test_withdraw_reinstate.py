from doajtest.helpers import DoajTestCase
from doajtest.fixtures import JournalFixtureFactory, ArticleFixtureFactory

from portality import models
from portality.tasks.journal_in_out_doaj import SetInDOAJBackgroundTask, change_in_doaj

import time

class TestWithdrawReinstate(DoajTestCase):

    def setUp(self):
        super(TestWithdrawReinstate, self).setUp()

    def tearDown(self):
        super(TestWithdrawReinstate, self).tearDown()

    def test_01_withdraw_task(self):
        sources = JournalFixtureFactory.make_many_journal_sources(10, in_doaj=True)
        ids = []
        articles = []
        for source in sources:
            j = models.Journal(**source)
            j.save()
            ids.append(j.id)

            pissn = j.bibjson().get_identifiers(j.bibjson().P_ISSN)
            eissn = j.bibjson().get_identifiers(j.bibjson().E_ISSN)
            asource = ArticleFixtureFactory.make_article_source(pissn=pissn[0], eissn=eissn[0], with_id=False)
            a = models.Article(**asource)
            a.save()
            articles.append(a.id)

        time.sleep(2)

        job = SetInDOAJBackgroundTask.prepare("testuser", journal_ids=ids, in_doaj=False)
        SetInDOAJBackgroundTask.submit(job)

        time.sleep(2)

        for id in ids:
            j = models.Journal.pull(id)
            assert j.is_in_doaj() is False

        for id in articles:
            a = models.Article.pull(id)
            assert a.is_in_doaj() is False

    def test_02_reinstate_task(self):
        sources = JournalFixtureFactory.make_many_journal_sources(10, in_doaj=False)
        ids = []
        articles = []
        for source in sources:
            j = models.Journal(**source)
            j.save()
            ids.append(j.id)

            pissn = j.bibjson().get_identifiers(j.bibjson().P_ISSN)
            eissn = j.bibjson().get_identifiers(j.bibjson().E_ISSN)
            asource = ArticleFixtureFactory.make_article_source(pissn=pissn[0], eissn=eissn[0], with_id=False, in_doaj=False)
            a = models.Article(**asource)
            a.save()
            articles.append(a.id)

        time.sleep(2)

        job = SetInDOAJBackgroundTask.prepare("testuser", journal_ids=ids, in_doaj=True)
        SetInDOAJBackgroundTask.submit(job)

        time.sleep(2)

        for id in ids:
            j = models.Journal.pull(id)
            assert j.is_in_doaj() is True

        for id in articles:
            a = models.Article.pull(id)
            assert a.is_in_doaj() is True

    def test_03_withdraw(self):
        acc = models.Account()
        acc.set_name("testuser")
        ctx = self._make_and_push_test_context(acc=acc)

        sources = JournalFixtureFactory.make_many_journal_sources(10, in_doaj=True)
        ids = []
        articles = []
        for source in sources:
            j = models.Journal(**source)
            j.save()
            ids.append(j.id)

            pissn = j.bibjson().get_identifiers(j.bibjson().P_ISSN)
            eissn = j.bibjson().get_identifiers(j.bibjson().E_ISSN)
            asource = ArticleFixtureFactory.make_article_source(pissn=pissn[0], eissn=eissn[0], with_id=False)
            a = models.Article(**asource)
            a.save()
            articles.append(a.id)

        time.sleep(2)

        change_in_doaj(ids, False)

        time.sleep(2)

        for id in ids:
            j = models.Journal.pull(id)
            assert j.is_in_doaj() is False

        for id in articles:
            a = models.Article.pull(id)
            assert a.is_in_doaj() is False

        ctx.pop()

    def test_04_reinstate(self):
        acc = models.Account()
        acc.set_name("testuser")
        ctx = self._make_and_push_test_context(acc=acc)

        sources = JournalFixtureFactory.make_many_journal_sources(10, in_doaj=False)
        ids = []
        articles = []
        for source in sources:
            j = models.Journal(**source)
            j.save()
            ids.append(j.id)

            pissn = j.bibjson().get_identifiers(j.bibjson().P_ISSN)
            eissn = j.bibjson().get_identifiers(j.bibjson().E_ISSN)
            asource = ArticleFixtureFactory.make_article_source(pissn=pissn[0], eissn=eissn[0], with_id=False, in_doaj=False)
            a = models.Article(**asource)
            a.save()
            articles.append(a.id)

        time.sleep(2)

        change_in_doaj(ids, True)

        time.sleep(2)

        for id in ids:
            j = models.Journal.pull(id)
            assert j.is_in_doaj() is True

        for id in articles:
            a = models.Article.pull(id)
            assert a.is_in_doaj() is True

        ctx.pop()