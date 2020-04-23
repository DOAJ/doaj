from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets

from doajtest.fixtures import ArticleFixtureFactory, AccountFixtureFactory, JournalFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.models import Article, Account, Journal
from portality.lib.paths import rel2abs
from doajtest.mocks.bll_article import BLLArticleMockFactory


EXCEPTIONS = {
    "ArgumentException": exceptions.ArgumentException,
    "DuplicateArticleException": exceptions.DuplicateArticleException,
    "ArticleNotAcceptable": exceptions.ArticleNotAcceptable
}

def prepare_update_admin_load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "article_create_article"), "prepare_update_admin",
                               "test_id",
                               {"test_id": []})


class TestBLLPrepareUpdatePublisher(DoajTestCase):

    def setUp(self):
        super(TestBLLPrepareUpdatePublisher, self).setUp()
        self.svc = DOAJ.articleService()
        self.is_id_updated = self.svc._doi_or_fulltext_updated
        self.merge = Article.merge
        self.pull = Article.pull

    def tearDown(self):

        super(TestBLLPrepareUpdatePublisher, self).tearDown()
        self.svc._doi_or_fulltext_updated = self.is_id_updated
        Article.merge = self.merge
        Article.pull = self.pull

    @parameterized.expand(prepare_update_admin_load_cases)
    def test_prepare_update_admin(self, value, kwargs):

        Article.merge = BLLArticleMockFactory.merge_mock
        Article.pull = BLLArticleMockFactory.pull_mock

        duplicate_arg = kwargs.get("duplicate")
        merge_duplicate_arg = kwargs.get("merge_duplicate")
        is_update_arg = kwargs.get("is_update")
        raises_arg = kwargs.get("raises")

        pissn1 = "1234-5678"
        eissn1 = "9876-5432"
        pissn2 = "1111-1111"
        eissn2 = "2222-2222"
        doi = "10.1234/article-10"
        ft = "https://example.com"

        update_article_id = "update_id"

        article_src = ArticleFixtureFactory.make_article_source(pissn=pissn1, eissn=eissn1, doi=doi, fulltext=ft)
        article = Article(**article_src)
        article.set_id("article_id")

        duplicate = None
        if duplicate_arg != "none":
            duplicate_src = ArticleFixtureFactory.make_article_source(pissn=pissn2, eissn=eissn2, doi=doi, fulltext=ft)
            duplicate = Article(**duplicate_src)
            if duplicate_arg == "same_as_update_article_id":
                duplicate.set_id("update_id")
            elif duplicate_arg == "different_then_update_article_id":
                duplicate.set_id("duplicate_id")

        merge_duplicate = True if merge_duplicate_arg == "yes" else False

        if raises_arg == "DuplicateArticle":
            with self.assertRaises(exceptions.DuplicateArticleException):
                self.svc._prepare_update_admin(article, duplicate, update_article_id, merge_duplicate)
        else:
            assert self.svc._prepare_update_admin(article, duplicate, update_article_id, merge_duplicate) == int(
                is_update_arg)