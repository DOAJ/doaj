from doajtest.fixtures import article_doajxml
from doajtest.helpers import DoajTestCase
from doajtest.unit_tester import article_upload_tester
from portality import models
from portality.tasks.helpers import articles_upload_helper, background_helper


class TestArticlesUploadHelper(DoajTestCase):

    def setUp(self):
        super().setUp()
        self.fix_es_mapping()

    def test_submit_success(self):
        article_upload_tester.test_submit_success(run_background_process_common)

    def test_fail_unmatched_issn(self):
        article_upload_tester.test_fail_unmatched_issn(run_background_process_common)

    def test_doaj_fail_shared_issn(self):
        article_upload_tester.test_fail_shared_issn(run_background_process_common)

    def test_fail_unowned_issn(self):
        article_upload_tester.test_fail_unowned_issn(run_background_process_common)

    def test_journal_2_article_2_success(self):
        article_upload_tester.test_journal_2_article_2_success(run_background_process_common)

    def test_journal_2_article_1_success(self):
        article_upload_tester.test_journal_2_article_1_success(run_background_process_common)

    def test_journal_1_article_1_success(self):
        article_upload_tester.test_journal_1_article_1_success(run_background_process_common)

    def test_journal_2_article_2_1_different_success(self):
        article_upload_tester.test_journal_2_article_2_1_different_success(run_background_process_common)

    def test_2_journals_different_owners_both_issns_fail(self):
        article_upload_tester.test_2_journals_different_owners_both_issns_fail(
            run_background_process_common)

    def test_2_journals_different_owners_issn_each_fail(self):
        article_upload_tester.test_2_journals_different_owners_issn_each_fail(
            run_background_process_common)

    def test_2_journals_same_owner_issn_each_fail(self):
        article_upload_tester.test_2_journals_same_owner_issn_each_fail(run_background_process_common)

    def test_2_journals_different_owners_different_issns_mixed_article_fail(self):
        article_upload_tester.test_2_journals_different_owners_different_issns_mixed_article_fail(
            run_background_process_common)

    def test_journal_1_article_1_superlong_noclip(self):
        article_upload_tester.test_journal_1_article_1_superlong_noclip(run_background_process_common)

    def test_45_journal_1_article_1_superlong_clip(self):
        article_upload_tester.test_journal_1_article_1_superlong_clip(run_background_process_common)

    def test_one_journal_one_article_2_issns_one_unknown(self):
        article_upload_tester.test_one_journal_one_article_2_issns_one_unknown(run_background_process_common)

    def test_lcc_spelling_error(self):
        article_upload_tester.test_lcc_spelling_error(run_background_process_common)

    def test_unknown_journal_issn(self):
        article_upload_tester.test_unknown_journal_issn(run_background_process_common)


def run_background_process_common(acc_id, handle):
    articles = article_doajxml.to_articles(handle)
    base_articles_upload = models.BulkArticles(owner=acc_id)
    articles_upload_helper.upload_process(
        base_articles_upload,
        background_helper.create_job(acc_id, '__action__'),
        articles,
        lambda _articles: _articles,
    )
    return base_articles_upload
