from copy import deepcopy
from unittest.mock import patch

from doajtest import helpers
from doajtest.fixtures import article_doajxml
from doajtest.helpers import DoajTestCase
from doajtest.unit_tester import article_upload_tester
from portality import models
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
        # #4343: one bad article in a batch must be identified, and nothing in the batch is saved
        acc_id = "testowner"
        helpers.save_all_block_last([
            article_upload_tester.create_simple_journal(acc_id, pissn="1234-5678", eissn="9876-5432"),
            article_upload_tester.create_simple_publisher(acc_id),
        ])
        article = article_doajxml.to_articles(article_doajxml.DoajXmlArticleFixtureFactory.upload_2_issns_correct())[0]
        articles = [deepcopy(article.data) for _ in range(3)]
        del articles[1]["bibjson"]["title"]
        articles[2] = {"invalid": "format"}

        bulk_articles = run_background_process_by_incoming_articles(acc_id, articles)

        article_upload_tester.assert_failed(bulk_articles, expected_details=False)
        assert "Article at index 0" not in bulk_articles.error
        assert "Article at index 1: Field 'title' is required" in bulk_articles.error
        assert "Article at index 2: " in bulk_articles.error
        assert bulk_articles.valid_but_not_imported == 1
        assert bulk_articles.failed_imports == 2
        assert models.Article.count() == 0

    def test_no_matching_journal_reported_with_counts(self):
        acc_id = "testowner"
        helpers.save_all_block_last([
            article_upload_tester.create_simple_journal(acc_id, pissn="1234-5678", eissn="9876-5432"),
            article_upload_tester.create_simple_publisher(acc_id),
        ])
        article = article_doajxml.to_articles(article_doajxml.DoajXmlArticleFixtureFactory.upload_2_issns_correct())[0]
        articles = [deepcopy(article.data) for _ in range(2)]
        articles[1]["bibjson"]["identifier"] = [{"type": "pissn", "id": "8888-8888"}, {"type": "eissn", "id": "9999-9999"}]

        bulk_articles = run_background_process_by_incoming_articles(acc_id, articles)

        assert "Article at index 1: No journal found" in bulk_articles.error
        assert bulk_articles.valid_but_not_imported == 1
        assert bulk_articles.failed_imports == 1
        assert models.Article.count() == 0

    def _setup_batch(self, n):
        acc_id = "testowner"
        helpers.save_all_block_last([
            article_upload_tester.create_simple_journal(acc_id, pissn="1234-5678", eissn="9876-5432"),
            article_upload_tester.create_simple_publisher(acc_id),
        ])
        article = article_doajxml.to_articles(article_doajxml.DoajXmlArticleFixtureFactory.upload_2_issns_correct())[0]
        return acc_id, [deepcopy(article.data) for _ in range(n)]

    def test_script_tags_send_one_email_per_upload(self):
        # #4343: every bad article is reported, but the recipients get a single warning email
        acc_id, articles = self._setup_batch(4)
        for a in articles[1:]:
            a["bibjson"]["title"] = "<script>x</script>"

        with patch("portality.api.current.crud.articles.app_email.send_mail") as send_mail:
            bulk_articles = run_background_process_by_incoming_articles(acc_id, articles)

        assert send_mail.call_count == 1
        for i in (1, 2, 3):
            assert f"Article at index {i}: " in bulk_articles.error
        assert bulk_articles.valid_but_not_imported == 1
        assert bulk_articles.failed_imports == 3

    def test_unexpected_error_does_not_hide_other_articles(self):
        acc_id, articles = self._setup_batch(3)
        del articles[2]["bibjson"]["title"]

        from portality.api.current import ArticlesCrudApi
        real = ArticlesCrudApi.prep_article
        calls = []

        def flaky(data, account, send_email=True):
            calls.append(1)
            if len(calls) == 2:
                raise RuntimeError("boom")
            return real(data, account, send_email=send_email)

        with patch.object(ArticlesCrudApi, "prep_article", side_effect=flaky):
            bulk_articles = run_background_process_by_incoming_articles(acc_id, articles)

        assert "Article at index 1: unexpected error" in bulk_articles.error
        assert "Article at index 2: Field 'title' is required" in bulk_articles.error
        assert "boom" not in bulk_articles.error
        assert bulk_articles.valid_but_not_imported == 1
        assert bulk_articles.failed_imports == 2
