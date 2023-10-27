import time

from doajtest.fixtures import JournalFixtureFactory, ArticleFixtureFactory, ApplicationFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import models, constants
from portality.tasks.journal_in_out_doaj import SetInDOAJBackgroundTask, change_in_doaj


class TestWithdrawReinstate(DoajTestCase):

    def setUp(self):
        super(TestWithdrawReinstate, self).setUp()

    def tearDown(self):
        super(TestWithdrawReinstate, self).tearDown()

    @staticmethod
    def make_account():
        account = models.Account.make_account(email="test@test.com", username="admin", name="admin",
                                              roles=["admin", "api"])
        account.set_password('password123')
        account.save(blocking=True)
        return account

    def test_01_withdraw_task(self):
        account = self.make_account()
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

        time.sleep(1)

        job = SetInDOAJBackgroundTask.prepare(account.id, journal_ids=ids, in_doaj=False)
        SetInDOAJBackgroundTask.submit(job)

        time.sleep(1)

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
            asource = ArticleFixtureFactory.make_article_source(pissn=pissn[0], eissn=eissn[0], with_id=False,
                                                                in_doaj=False)
            a = models.Article(**asource)
            a.save()
            articles.append(a.id)

        time.sleep(1)

        job = SetInDOAJBackgroundTask.prepare("testuser", journal_ids=ids, in_doaj=True)
        SetInDOAJBackgroundTask.submit(job)

        time.sleep(1)

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

        articles, ids = make_journals_for_withdraw()

        change_in_doaj(ids, False)

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
            asource = ArticleFixtureFactory.make_article_source(pissn=pissn[0], eissn=eissn[0], with_id=False,
                                                                in_doaj=False)
            a = models.Article(**asource)
            a.save()
            articles.append(a.id)

        time.sleep(1)

        change_in_doaj(ids, True)

        for id in ids:
            j = models.Journal.pull(id)
            assert j.is_in_doaj() is True

        for id in articles:
            a = models.Article.pull(id)
            assert a.is_in_doaj() is True

        ctx.pop()

    def test_05_withdraw_with_ur(self):
        account = self.make_account()

        UPDATE_REQUEST_SOURCE = ApplicationFixtureFactory.make_update_request_source()
        JOURNAL_SOURCE = JournalFixtureFactory.make_journal_source(in_doaj=True)
        JOURNAL_SOURCE["admin"]["current_application"] = UPDATE_REQUEST_SOURCE["id"]
        UPDATE_REQUEST_SOURCE["admin"]["current_journal"] = JOURNAL_SOURCE["id"]
        j = models.Journal(**JOURNAL_SOURCE)
        j.save()

        application = models.Application(**UPDATE_REQUEST_SOURCE)
        application.save()

        time.sleep(1)

        job = SetInDOAJBackgroundTask.prepare(account.id, journal_ids=[j.id], in_doaj=False)
        SetInDOAJBackgroundTask.submit(job)

        time.sleep(1)

        j = models.Journal.pull(j.id)
        assert j.is_in_doaj() is False

        ur = models.Application.pull(application.id)
        assert ur.application_status == constants.APPLICATION_STATUS_REJECTED, "application status: {}, expected: {}".format(
            ur.application_status, constants.APPLICATION_STATUS_REJECTED)

    def test_06_withdraw_with_trigger_by_jid(self):
        with self._make_and_push_test_context_manager(acc=self.make_account()):
            _, journal_ids = make_journals_for_withdraw()

            trigger_by_jid = journal_ids[0]
            change_in_doaj(journal_ids, False, trigger_by_jid=trigger_by_jid)
            assert_journals_withdrawn(journal_ids, trigger_by_jid)

    def test_07_withdraw_without_trigger_by_jid(self):
        with self._make_and_push_test_context_manager(acc=self.make_account()):
            _, journal_ids = make_journals_for_withdraw()

            trigger_by_jid = None
            change_in_doaj(journal_ids, False, trigger_by_jid=trigger_by_jid)
            assert_journals_withdrawn(journal_ids, trigger_by_jid)


def make_test_account():
    acc = models.Account()
    acc.set_name("testuser")
    return acc


def make_journals_for_withdraw():
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
    time.sleep(1)
    return articles, ids


def has_auto_msg(j):
    return any(['Journal automatically withdrawn due to' in n['note'] for n in j.notes])


def assert_journals_withdrawn(journal_ids, trigger_by_jid):
    for id in journal_ids:
        j = models.Journal.pull(id)
        if trigger_by_jid is None:
            assert not has_auto_msg(j)
        else:
            if id == trigger_by_jid:
                assert not has_auto_msg(j)
            else:
                assert has_auto_msg(j)

        assert j.is_in_doaj() is False
