from time import sleep
import json

from doajtest.helpers import DoajTestCase

from flask_login import logout_user

from portality import models
from portality.background import BackgroundException
from portality.tasks.journal_bulk_delete import journal_bulk_delete_manage, JournalBulkDeleteBackgroundTask

from doajtest.fixtures import JournalFixtureFactory, AccountFixtureFactory, ArticleFixtureFactory

TEST_JOURNAL_COUNT = 25
TEST_ARTICLES_PER_JOURNAL = 2

class TestTaskJournalBulkDelete(DoajTestCase):

    def setUp(self):
        super(TestTaskJournalBulkDelete, self).setUp()

        self.journals = []
        self.articles = []
        for j_src in JournalFixtureFactory.make_many_journal_sources(count=TEST_JOURNAL_COUNT):
            j = models.Journal(**j_src)
            self.journals.append(j)
            j.save()
            for i in range(0, TEST_ARTICLES_PER_JOURNAL):
                a = models.Article(**ArticleFixtureFactory.make_article_source(with_id=False, eissn=j.bibjson().first_eissn, pissn=j.bibjson().first_pissn))
                a.save()
                self.articles.append(a)
        self.journals[-1].snapshot()
        self.articles[-1].snapshot()
        sleep(2)

        self.forbidden_accounts = [
            AccountFixtureFactory.make_editor_source()['id'],
            AccountFixtureFactory.make_assed1_source()['id'],
            AccountFixtureFactory.make_assed2_source()['id'],
            AccountFixtureFactory.make_assed3_source()['id']
        ]

        self._make_and_push_test_context(acc=models.Account(**AccountFixtureFactory.make_managing_editor_source()))

    def tearDown(self):
        super(TestTaskJournalBulkDelete, self).tearDown()

    def test_01_bulk_delete(self):
        """Bulk delete journals as an admin"""
        # test dry run
        r = journal_bulk_delete_manage({"query": {"terms": {"_id": [j.id for j in self.journals]}}}, dry_run=True)
        assert r == {'journals-to-be-deleted': TEST_JOURNAL_COUNT, 'articles-to-be-deleted': TEST_JOURNAL_COUNT * TEST_ARTICLES_PER_JOURNAL}, r

        r = journal_bulk_delete_manage({"query": {"terms": {"_id": [j.id for j in self.journals]}}}, dry_run=False)
        assert r is True, r

        sleep(3)

        job = models.BackgroundJob.all()[0]

        assert len(models.Journal.all()) == 0, "{}\n\n{}".format(len(models.Journal.all()), json.dumps(job.audit, indent=2))  # json.dumps([j.data for j in models.Journal.all()], indent=2)
        assert len(models.Article.all()) == 0, "{}\n\n{}".format(len(models.Article.all()), json.dumps(job.audit, indent=2))  # json.dumps([a.data for a in models.Article.all()], indent=2)
