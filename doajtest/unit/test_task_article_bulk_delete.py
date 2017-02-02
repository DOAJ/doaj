from time import sleep
import json

from doajtest.helpers import DoajTestCase

from portality import models
from portality.tasks.article_bulk_delete import article_bulk_delete_manage

from doajtest.fixtures import JournalFixtureFactory, AccountFixtureFactory, ArticleFixtureFactory

TEST_JOURNAL_COUNT = 2
TEST_ARTICLES_PER_JOURNAL = 25

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

        sleep(2)

        self._make_and_push_test_context(acc=models.Account(**AccountFixtureFactory.make_managing_editor_source()))

    def tearDown(self):
        super(TestTaskJournalBulkDelete, self).tearDown()

    def test_01_bulk_delete(self):
        """Bulk delete journals as an admin, but leave some around to test queries in bulk delete job"""
        # test dry run

        # all articles with the last journal's ISSN. The articles for the other journal should remain intact.
        del_q_should_terms = {"query": {"bool": {"must": [{"match_all": {}}, {"terms": {"index.issn.exact": [self.journals[-1].bibjson().first_pissn]}}]}}}

        r = article_bulk_delete_manage(del_q_should_terms, dry_run=True)
        assert r == 1 * TEST_ARTICLES_PER_JOURNAL, r

        r = article_bulk_delete_manage(del_q_should_terms, dry_run=False)
        assert r is True, r

        sleep(3)

        job = models.BackgroundJob.all()[0]

        assert len(models.Journal.all()) == TEST_JOURNAL_COUNT, "{}\n\n{}".format(len(models.Journal.all()), json.dumps(job.audit, indent=2))  # json.dumps([j.data for j in models.Journal.all()], indent=2)
        assert len(models.Article.all()) == 1 * TEST_ARTICLES_PER_JOURNAL, "{}\n\n{}".format(len(models.Article.all()), json.dumps(job.audit, indent=2))  # json.dumps([a.data for a in models.Article.all()], indent=2)
