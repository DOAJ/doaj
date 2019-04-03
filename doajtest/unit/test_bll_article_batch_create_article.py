from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets

from doajtest.fixtures import ArticleFixtureFactory, AccountFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.models import Article, Account
from portality.lib.paths import rel2abs
from doajtest.mocks.bll_article import BLLArticleMockFactory
from portality.dao import ESMappingMissingError

import time

def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "article_batch_create_article"), "batch_create_article", "test_id",
                               {"test_id" : []})

EXCEPTIONS = {
    "ArgumentException" : exceptions.ArgumentException,
    "DuplicateArticleException" : exceptions.DuplicateArticleException,
    "IngestException" : exceptions.IngestException
}

class TestBLLArticleBatchCreateArticle(DoajTestCase):

    def setUp(self):
        super(TestBLLArticleBatchCreateArticle, self).setUp()
        self.svc = DOAJ.articleService()
        self._is_legitimate_owner = self.svc.is_legitimate_owner
        self._get_duplicate = self.svc.get_duplicate
        self._issn_ownership_status = self.svc.issn_ownership_status


    def tearDown(self):
        self.svc.is_legitimate_owner = self._is_legitimate_owner
        self.svc.get_duplicate = self._get_duplicate
        self.svc.issn_ownership_status = self._issn_ownership_status
        super(TestBLLArticleBatchCreateArticle, self).tearDown()

    @parameterized.expand(load_cases)
    def test_01_batch_create_article(self, name, kwargs):

        articles_arg = kwargs.get("articles")
        duplicate_in_batch_arg = kwargs.get("duplicate_in_batch")
        duplicate_in_index_arg = kwargs.get("duplicate_in_index")
        account_arg = kwargs.get("account")
        duplicate_check_arg = kwargs.get("duplicate_check")
        merge_duplicate_arg = kwargs.get("merge_duplicate")
        limit_to_account_arg = kwargs.get("limit_to_account")

        raises_arg = kwargs.get("raises")
        success_arg = kwargs.get("success")
        fail_arg = kwargs.get("fail")
        update_arg = kwargs.get("update")

        ###############################################
        ## set up

        success = int(success_arg)
        fail = int(fail_arg)
        update = int(update_arg)

        duplicate_in_batch = duplicate_in_batch_arg == "yes"
        duplicate_in_index = duplicate_in_index_arg == "yes"

        raises = EXCEPTIONS.get(raises_arg)

        duplicate_check = None
        if duplicate_check_arg != "none":
            duplicate_check = True if duplicate_check_arg == "true" else False

        merge_duplicate = None
        if merge_duplicate_arg != "none":
            merge_duplicate = True if merge_duplicate_arg == "true" else False

        limit_to_account = None
        if limit_to_account_arg != "none":
            limit_to_account = True if limit_to_account_arg == "true" else False

        account = None
        if account_arg != "none":
            source = AccountFixtureFactory.make_publisher_source()
            account = Account(**source)

        last_doi = None
        last_ft = None
        last_issn = None
        last_id = None
        articles = None
        if articles_arg != "none":
            articles = []
            article_count = int(articles_arg)
            for i in range(article_count):
                idx = str(i)
                if duplicate_in_batch:
                    if i < 2:
                        idx = "duplicate"
                last_issn = str(i) * 4 + "-" + str(i) * 4
                last_doi = "10.123/abc/" + idx
                last_ft = "http://example.com/" + idx
                source = ArticleFixtureFactory.make_article_source(eissn=last_issn, pissn=last_issn, doi=last_doi, fulltext=last_ft)
                article = Article(**source)
                article.set_id()
                last_id = article.id
                articles.append(article)


        ilo_mock = None
        if account_arg == "owner":
            ilo_mock = BLLArticleMockFactory.is_legitimate_owner(legit=True)
        elif account_arg == "own_1":
            ilo_mock = BLLArticleMockFactory.is_legitimate_owner(legit_on_issn=[last_issn])
        else:
            ilo_mock = BLLArticleMockFactory.is_legitimate_owner()
        self.svc.is_legitimate_owner = ilo_mock

        gd_mock = None
        if duplicate_in_index:
            gd_mock = BLLArticleMockFactory.get_duplicate(given_article_id=last_id, eissn=last_issn, pissn=last_issn, doi=last_doi, fulltext=last_ft)
        else:
            gd_mock = BLLArticleMockFactory.get_duplicate(return_none=True)
        self.svc.get_duplicate = gd_mock

        ios_mock = BLLArticleMockFactory.issn_ownership_status([], [], [], [])
        self.svc.issn_ownership_status = ios_mock

        ###########################################################
        # Execution

        if raises is not None:
            with self.assertRaises(raises):
                try:
                    self.svc.batch_create_articles(articles, account, duplicate_check, merge_duplicate, limit_to_account)
                except exceptions.IngestException as e:
                    report = e.result
                    assert report["success"] == success
                    assert report["fail"] == fail
                    assert report["update"] == update
                    assert report["new"] == success - update
                    raise
        else:
            report = self.svc.batch_create_articles(articles, account, duplicate_check, merge_duplicate, limit_to_account)

            # make sure all the articles are saved before running the asserts
            aids = [(a.id, a.last_updated) for a in articles]
            for aid, lu in aids:
                Article.block(aid, lu, sleep=0.05)

            assert report["success"] == success
            assert report["fail"] == fail
            assert report["update"] == update
            assert report["new"] == success - update

            if success > 0:
                all_articles = Article.all()
                if len(all_articles) != success:
                    time.sleep(0.5)
                    all_articles = Article.all()
                assert len(all_articles) == success

            else:
                # there's nothing in the article index
                with self.assertRaises(ESMappingMissingError):
                    Article.all()