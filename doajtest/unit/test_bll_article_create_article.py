from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets

from doajtest.fixtures import ArticleFixtureFactory, AccountFixtureFactory, JournalFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.models import Article, Account, Journal
from portality.lib.paths import rel2abs
from doajtest.mocks.bll_article import BLLArticleMockFactory

def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "article_create_article"), "create_article", "test_id",
                               {"test_id" : []})

EXCEPTIONS = {
    "ArgumentException" : exceptions.ArgumentException,
    "DuplicateArticleException" : exceptions.DuplicateArticleException,
    "ArticleNotAcceptable" : exceptions.ArticleNotAcceptable
}

class TestBLLArticleCreateArticle(DoajTestCase):

    def setUp(self):
        super(TestBLLArticleCreateArticle, self).setUp()
        self.svc = DOAJ.articleService()
        self._is_legitimate_owner = self.svc.is_legitimate_owner
        self._issn_ownership_status = self.svc.issn_ownership_status
        self._get_duplicate = self.svc.get_duplicate

    def tearDown(self):
        self.svc.is_legitimate_owner = self._is_legitimate_owner
        self.svc.issn_ownership_status = self._issn_ownership_status
        self.svc.get_duplicate = self._get_duplicate
        super(TestBLLArticleCreateArticle, self).tearDown()

    @parameterized.expand(load_cases)
    def test_01_create_article(self, name, kwargs):

        article_arg = kwargs.get("article")
        has_ids_arg = kwargs.get("has_ids")
        article_duplicate_arg = kwargs.get("article_duplicate")
        account_arg = kwargs.get("account")
        duplicate_check_arg = kwargs.get("duplicate_check")
        merge_duplicate_arg = kwargs.get("merge_duplicate")
        limit_to_account_arg = kwargs.get("limit_to_account")
        add_journal_info_arg = kwargs.get("add_journal_info")
        dry_run_arg = kwargs.get("dry_run")

        raises_arg = kwargs.get("raises")
        success_arg = kwargs.get("success")
        original_saved_arg = kwargs.get("original_saved")
        merge_saved_arg = kwargs.get("merge_saved")

        ###############################################
        ## set up

        has_doi = has_ids_arg == "doi+ft"
        has_ft = has_ids_arg == "doi+ft"
        success = int(success_arg)

        duplicate_check = None
        if duplicate_check_arg != "none":
            duplicate_check = True if duplicate_check_arg == "true" else False

        merge_duplicate = None
        if merge_duplicate_arg != "none":
            merge_duplicate = True if merge_duplicate_arg == "true" else False

        limit_to_account = None
        if limit_to_account_arg != "none":
            limit_to_account = True if limit_to_account_arg == "true" else False

        add_journal_info = None
        if add_journal_info_arg != "none":
            add_journal_info = True if add_journal_info_arg == "true" else False

        dry_run = None
        if dry_run_arg != "none":
            dry_run = True if dry_run_arg == "true" else False

        raises = EXCEPTIONS.get(raises_arg)

        eissn = "1234-5678"
        pissn = "9876-5432"
        doi = "10.123/abc/1"
        fulltext = "http://example.com/1"

        if add_journal_info:
            jsource = JournalFixtureFactory.make_journal_source(in_doaj=True)
            j = Journal(**jsource)
            bj = j.bibjson()
            bj.title = "Add Journal Info Title"
            bj.remove_identifiers()
            bj.add_identifier(bj.P_ISSN, pissn)
            bj.add_identifier(bj.E_ISSN, eissn)
            j.save(blocking=True)

        article = None
        original_id = None
        if article_arg == "exists":
            this_doi = doi if has_doi else False
            this_fulltext = fulltext if has_ft else False
            source = ArticleFixtureFactory.make_article_source(eissn=eissn, pissn=pissn, doi=this_doi, fulltext=this_fulltext)
            del source["bibjson"]["journal"]
            article = Article(**source)
            article.set_id()
            original_id = article.id

        account = None
        if account_arg != "none":
            source = AccountFixtureFactory.make_publisher_source()
            account = Account(**source)

        legit = True if account_arg == "owner" else False
        ilo_mock = BLLArticleMockFactory.is_legitimate_owner(legit=legit)
        self.svc.is_legitimate_owner = ilo_mock

        owned = [eissn, pissn] if account_arg == "owner" else []
        shared = []
        unowned = [eissn] if account_arg == "not_owner" else []
        unmatched = [pissn] if account_arg == "not_owner" else []
        ios_mock = BLLArticleMockFactory.issn_ownership_status(owned, shared, unowned, unmatched)
        self.svc.issn_ownership_status = ios_mock

        gd_mock = None
        if article_duplicate_arg == "yes":
            gd_mock = BLLArticleMockFactory.get_duplicate(eissn=eissn, pissn=pissn, doi="10.123/abc/1", fulltext="http://example.com/1")
        else:
            gd_mock = BLLArticleMockFactory.get_duplicate(return_none=True)
        self.svc.get_duplicate = gd_mock

        mock_article = self.svc.get_duplicate(article)

        ###########################################################
        # Execution

        if raises is not None:
            with self.assertRaises(raises):
                self.svc.create_article(article, account, duplicate_check, merge_duplicate,
                                        limit_to_account, add_journal_info, dry_run)
        else:
            report = self.svc.create_article(article, account, duplicate_check, merge_duplicate,
                                             limit_to_account, add_journal_info, dry_run)

            assert report["success"] == success

            # check that the article was saved and if it was saved that it was suitably merged
            if original_saved_arg == "yes":
                original = Article.pull(original_id)
                assert original is not None
                assert report["update"] == 0
            elif article is not None:
                original = Article.pull(original_id)
                assert original is None

            if merge_saved_arg == "yes":
                merged = Article.pull(mock_article.id)
                assert merged is not None
                assert report["update"] == 1
            elif mock_article is not None:
                merged = Article.pull(mock_article.id)
                assert merged is None

            if add_journal_info:
                assert article.bibjson().journal_title == "Add Journal Info Title"

