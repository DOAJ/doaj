from doajtest.helpers import DoajTestCase
from doajtest.fixtures import JournalFixtureFactory, ArticleFixtureFactory, ApplicationFixtureFactory
from flask_login import current_user

from portality import models, constants
from portality.tasks.journal_in_out_doaj import SetInDOAJBackgroundTask, change_in_doaj

import time

class TestWithdrawReinstate(DoajTestCase):

    def setUp(self):
        super(TestWithdrawReinstate, self).setUp()

    def tearDown(self):
        super(TestWithdrawReinstate, self).tearDown()

    @staticmethod
    def login(app, username, password):
        return app.post('/account/login',
                        data=dict(user=username, password=password),
                        follow_redirects=True)

    @staticmethod
    def logout(app):
        return app.get('/account/logout', follow_redirects=True)

    @staticmethod
    def make_account():
        account = models.Account.make_account(email="test@test.com", username="admin", name="admin",
                                              roles=["admin", "api"])
        account.set_password('password123')
        account.save(blocking=True)

    def test_01_withdraw_task(self):
        self.make_account()
        sources = JournalFixtureFactory.make_many_journal_sources(10, in_doaj=True)
        ids = []
        articles = []
        for source in sources:
            source["admin"]["current_application"] = ""
            j = models.Journal(**source)
            j.save()
            ids.append(j.id)

            pissn = j.bibjson().get_identifiers(j.bibjson().P_ISSN)
            eissn = j.bibjson().get_identifiers(j.bibjson().E_ISSN)
            asource = ArticleFixtureFactory.make_article_source(pissn=pissn[0], eissn=eissn[0], with_id=False)
            a = models.Article(**asource)
            a.save()
            articles.append(a.id)

            UPDATE_REQUEST_SOURCE_TEST_1 = ApplicationFixtureFactory.make_update_request_source()
            application = models.Application(**UPDATE_REQUEST_SOURCE_TEST_1)

        time.sleep(2)

        with self.app_test.test_client() as t_client:
            resp = self.login(t_client, "admin", "password123")
            job = SetInDOAJBackgroundTask.prepare("admin", journal_ids=ids, in_doaj=False)
            SetInDOAJBackgroundTask.submit(job)
            self.logout(t_client)

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
        self.make_account()
        acc = models.Account()
        acc.set_name("testuser")
        ctx = self._make_and_push_test_context(acc=acc)

        sources = JournalFixtureFactory.make_many_journal_sources(10, in_doaj=True)
        ids = []
        articles = []
        for source in sources:
            source["admin"]["current_application"] = ""
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

        with self.app_test.test_client() as t_client:
            resp = self.login(t_client, "admin", "password123")
            change_in_doaj(ids, False)

            time.sleep(2)
            self.logout(t_client)

        for id in ids:
            j = models.Journal.pull(id)
            assert j.is_in_doaj() is False

        for id in articles:
            a = models.Article.pull(id)
            assert a.is_in_doaj() is False

        ctx.pop()

    def test_04_reinstate(self):
        self.make_account()

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

        with self.app_test.test_client() as t_client:
            resp = self.login(t_client, "admin", "password123")
            change_in_doaj(ids, True)
            self.logout(t_client)
            time.sleep(2)

        for id in ids:
            j = models.Journal.pull(id)
            assert j.is_in_doaj() is True

        for id in articles:
            a = models.Article.pull(id)
            assert a.is_in_doaj() is True

        ctx.pop()

    def test_05_withdraw_with_ur(self):
        self.make_account()

        UPDATE_REQUEST_SOURCE = ApplicationFixtureFactory.make_update_request_source()
        JOURNAL_SOURCE = JournalFixtureFactory.make_journal_source(in_doaj=True)
        JOURNAL_SOURCE["admin"]["current_application"] = UPDATE_REQUEST_SOURCE["id"]
        UPDATE_REQUEST_SOURCE["admin"]["current_journal"] = JOURNAL_SOURCE["id"]
        j = models.Journal(**JOURNAL_SOURCE)
        j.save()

        application = models.Application(**UPDATE_REQUEST_SOURCE)
        application.save()

        time.sleep(2)

        with self.app_test.test_client() as t_client:
            resp = self.login(t_client, "admin", "password123")

            job = SetInDOAJBackgroundTask.prepare("admin", journal_ids=[j.id], in_doaj=False)
            SetInDOAJBackgroundTask.submit(job)

            self.logout(t_client)

        time.sleep(2)

        j = models.Journal.pull(j.id)
        assert j.is_in_doaj() is False

        ur = models.Application.pull(application.id)
        assert ur.application_status == constants.APPLICATION_STATUS_REJECTED, "application status: {}, expected: {}".format(ur.application_status, constants.APPLICATION_STATUS_REJECTED)
