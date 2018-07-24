from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets

from doajtest.fixtures import ArticleFixtureFactory, AccountFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.models import Article, Journal, Account
from portality.lib.paths import rel2abs
from doajtest.mocks.bll_article import BLLArticleMockFactory

def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "article_create_article"), "create_article", "test_id",
                               {"test_id" : []})


EXCEPTIONS = {
    "ArgumentException" : exceptions.ArgumentException,
    "DuplicateArticleException" : exceptions.DuplicateArticleException
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
        article_duplicate_arg = kwargs.get("article_duplicate")
        account_arg = kwargs.get("account")
        duplicate_check_arg = kwargs.get("duplicate_check")
        merge_duplicate_arg = kwargs.get("merge_duplicate")
        limit_to_account_arg = kwargs.get("limit_to_account")
        dry_run_arg = kwargs.get("dry_run")

        raises_arg = kwargs.get("raises")
        success_arg = kwargs.get("success")

        ###############################################
        ## set up

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

        dry_run = None
        if dry_run_arg != "none":
            dry_run = True if dry_run_arg == "true" else False

        raises = EXCEPTIONS.get(raises_arg)

        article = None
        if article_arg == "exists":
            source = ArticleFixtureFactory.make_article_source(eissn="1234-5678", pissn="9876-5432", doi="10.123/abc/1", fulltext="http://example.com/1")
            article = Article(**source)
            article.set_id()

        account = None
        if account_arg != "none":
            source = AccountFixtureFactory.make_publisher_source()
            account = Account(**source)

        legit = True if account_arg == "owner" else False
        ilo_mock = BLLArticleMockFactory.is_legitimate_owner(legit=legit)
        self.svc.is_legitimate_owner = ilo_mock

        owned = ["1234-5678", "9876-5432"] if account_arg == "owner" else []
        shared = []
        unowned = ["1234-5678"] if account_arg == "not_owner" else []
        unmatched = ["9876-5432"] if account_arg == "not_owner" else []
        ios_mock = BLLArticleMockFactory.issn_ownership_status(owned, shared, unowned, unmatched)
        self.svc.issn_ownership_status = ios_mock

        gd_mock = None
        if article_duplicate_arg == "yes":
            gd_mock = BLLArticleMockFactory.get_duplicate(eissn="1234-5678", pissn="9876-5432", doi="10.123/abc/1", fulltext="http://example.com/1")
        else:
            gd_mock = BLLArticleMockFactory.get_duplicate(eissn="6789-1234", pissn="4321-5678", doi="10.123/abc/2", fulltext="http://example.com/2")
        self.svc.get_duplicate = gd_mock

        ###########################################################
        # Execution

        if raises is not None:
            with self.assertRaises(raises):
                self.svc.create_article(article, account, duplicate_check, merge_duplicate, limit_to_account, dry_run)
        else:
            report = self.svc.create_article(article, account, duplicate_check, merge_duplicate, limit_to_account, dry_run)

            assert report["success"] == success
