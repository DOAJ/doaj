from doajtest import helpers
from doajtest.fixtures import article_doajxml
from doajtest.fixtures import ArticleFixtureFactory, JournalFixtureFactory
from doajtest.helpers import DoajTestCase
from doajtest.unit_tester import article_upload_tester
from portality.models import BulkArticles
from portality.tasks.article_bulk_create import ArticleBulkCreateBackgroundTask


def run_background_process_simple(acc_id, handle):
    articles = article_doajxml.to_articles(handle)
    articles = [article.data for article in articles]
    return run_background_process_by_incoming_articles(acc_id, articles)


def run_background_process_by_incoming_articles(acc_id, articles):
    job = ArticleBulkCreateBackgroundTask.prepare(acc_id, incoming_articles=articles)
    task = ArticleBulkCreateBackgroundTask(job)
    task.run()
    bulk_articles = BulkArticles.pull(task.get_param(job.params, "upload_id"))
    return bulk_articles


class TestArticleBulkCreateBackgroundTask(DoajTestCase):
    def setUp(self):
        super().setUp()
        self.fix_es_mapping()

    def test_submit_success(self):
        article_upload_tester.test_submit_success(run_background_process_simple)

    def test_fail_shared_issn(self):
        article_upload_tester.test_fail_shared_issn(run_background_process_simple)

    def test_invalid_income_articles_format(self):
        acc_id = "testowner"
        helpers.save_all_block_last([
            article_upload_tester.create_simple_publisher(acc_id),
        ])
        bulk_articles = run_background_process_by_incoming_articles(acc_id, [{"invalid": "format"}])
        article_upload_tester.assert_failed(bulk_articles, expected_details=False)

    def test_invalid_articles_reported_by_index(self):
        acc_id = "testowner"
        journal = JournalFixtureFactory.make_legacy_journal_object(in_doaj=True)
        journal.set_owner(acc_id)
        helpers.save_all_block_last([
            journal,
            article_upload_tester.create_simple_publisher(acc_id),
        ])
        articles = list(ArticleFixtureFactory.make_bulk_incoming_api_article(count=4))
        del articles[1]["bibjson"]["title"]
        del articles[2]["bibjson"]["title"]
        for ident in articles[3]["bibjson"]["identifier"]:
            if ident["type"] in ("pissn", "eissn"):
                ident["id"] = "0000-0000" if ident["type"] == "pissn" else "1111-1111"
        bulk_articles = run_background_process_by_incoming_articles(acc_id, articles)
        article_upload_tester.assert_failed(bulk_articles, expected_details=False)
        assert "index 0" not in bulk_articles.error
        assert "Article at index 1: Field 'title' is required" in bulk_articles.error
        assert "Article at index 2: Field 'title' is required" in bulk_articles.error
        assert "Article at index 3: No journal found" in bulk_articles.error
