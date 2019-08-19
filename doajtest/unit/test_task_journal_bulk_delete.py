from time import sleep
import json

from doajtest.helpers import DoajTestCase
from portality import models
from portality.tasks.journal_bulk_delete import journal_bulk_delete_manage

from doajtest.fixtures import JournalFixtureFactory, AccountFixtureFactory, DoajXmlArticleFixtureFactory

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
                a = models.Article(**DoajXmlArticleFixtureFactory.make_article_source(with_id=False, eissn=j.bibjson().first_eissn, pissn=j.bibjson().first_pissn))
                a.save()
                self.articles.append(a)

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
        """Bulk delete journals as an admin, but leave some around to test queries in bulk delete job"""
        # test dry run
        SPARE_JOURNALS_NUM = 5
        ids_to_delete = []
        for i in range(0, len(self.journals) - SPARE_JOURNALS_NUM):
            ids_to_delete.append(self.journals[i].id)
        del_q_should_terms = {"query": {"bool": {"must": [{"match_all": {}}, {"terms": {"_id": ids_to_delete}}]}}}

        summary = journal_bulk_delete_manage(del_q_should_terms, dry_run=True)
        assert summary.as_dict().get("affected", {}).get("journals") == TEST_JOURNAL_COUNT - SPARE_JOURNALS_NUM
        assert summary.as_dict().get("affected", {}).get("articles") == (TEST_JOURNAL_COUNT - SPARE_JOURNALS_NUM) * TEST_ARTICLES_PER_JOURNAL

        summary = journal_bulk_delete_manage(del_q_should_terms, dry_run=False)
        assert summary.as_dict().get("affected", {}).get("journals") == TEST_JOURNAL_COUNT - SPARE_JOURNALS_NUM
        assert summary.as_dict().get("affected", {}).get("articles") == (TEST_JOURNAL_COUNT - SPARE_JOURNALS_NUM) * TEST_ARTICLES_PER_JOURNAL

        sleep(3)

        job = models.BackgroundJob.all()[0]

        assert len(models.Journal.all()) == SPARE_JOURNALS_NUM, "{}\n\n{}".format(len(models.Journal.all()), json.dumps(job.audit, indent=2))  # json.dumps([j.data for j in models.Journal.all()], indent=2)
        assert len(models.Article.all()) == SPARE_JOURNALS_NUM * TEST_ARTICLES_PER_JOURNAL, "{}\n\n{}".format(len(models.Article.all()), json.dumps(job.audit, indent=2))  # json.dumps([a.data for a in models.Article.all()], indent=2)
