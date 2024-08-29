from doajtest import helpers
from doajtest.fixtures import article_doajxml
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
