from time import sleep
import json

from doajtest.helpers import DoajTestCase

from portality import models
from portality.tasks.article_bulk_delete import article_bulk_delete_manage, ArticleBulkDeleteBackgroundTask

from doajtest.fixtures import JournalFixtureFactory, AccountFixtureFactory, DoajXmlArticleFixtureFactory

TEST_JOURNAL_COUNT = 2
TEST_ARTICLES_PER_JOURNAL = 25

class TestTaskJournalBulkDelete(DoajTestCase):

    def setUp(self):
        super(TestTaskJournalBulkDelete, self).setUp()

        ArticleBulkDeleteBackgroundTask.BATCH_SIZE = 13

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

        self._make_and_push_test_context(acc=models.Account(**AccountFixtureFactory.make_managing_editor_source()))

    def tearDown(self):
        super(TestTaskJournalBulkDelete, self).tearDown()

    def test_01_bulk_delete(self):
        """Bulk delete journals as an admin, but leave some around to test queries in bulk delete job"""

        # all articles with the last journal's ISSN. The articles for the other journal should remain intact.
        del_q_should_terms = {"query": {"bool": {"must": [{"match_all": {}}, {"terms": {"index.issn.exact": [self.journals[-1].bibjson().first_pissn]}}]}}}

        summary = article_bulk_delete_manage(del_q_should_terms, dry_run=True)
        assert summary.as_dict().get("affected", {}).get("articles") == 1 * TEST_ARTICLES_PER_JOURNAL, summary.as_dict()

        summary = article_bulk_delete_manage(del_q_should_terms, dry_run=False)
        assert summary.as_dict().get("affected", {}).get("articles") == TEST_ARTICLES_PER_JOURNAL

        sleep(3)

        job = models.BackgroundJob.all()[0]

        audit_log = json.dumps(job.audit, indent=2)

        assert len(models.Journal.all()) == TEST_JOURNAL_COUNT, "{}\n\n{}".format(len(models.Journal.all()), audit_log)  # json.dumps([j.data for j in models.Journal.all()], indent=2)
        assert len(models.Article.all()) == 1 * TEST_ARTICLES_PER_JOURNAL, "{}\n\n{}".format(len(models.Article.all()), audit_log)  # json.dumps([a.data for a in models.Article.all()], indent=2)

        assert "About to delete 25 articles in 2 batches" in audit_log
        assert "Deleted 13 articles in batch 1 of 2" in audit_log
        assert "Deleted 12 articles in batch 2 of 2" in audit_log
        assert "Deleted 25 articles" in audit_log
