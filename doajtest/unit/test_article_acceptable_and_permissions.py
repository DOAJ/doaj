from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets

from doajtest.fixtures import ArticleFixtureFactory, AccountFixtureFactory, JournalFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.models import Article, Account, Journal
from portality.lib.paths import rel2abs


def is_acceptable_load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "article_create_article"), "is_acceptable",
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

    @parameterized.expand(is_acceptable_load_cases)
    def test_is_acceptable(self, value, kwargs):
        doi_arg = kwargs.get("doi")
        ft_arg = kwargs.get("fulltext_url")
        is_acceptable_arg = kwargs.get("is_acceptable")

        is_acceptable = True if is_acceptable_arg == "yes" else False
        doi = "10.1234/article-10" if doi_arg == "exists" else None
        ft = "https://example.com" if ft_arg == "exists" else None

        article_source = ArticleFixtureFactory.make_article_source()
        article = Article(**article_source)

        if doi is None:
            article.bibjson().remove_identifiers("doi")
        if ft is None:
            article.bibjson().remove_urls("fulltext")

        if is_acceptable:
            self.assertIsNone(self.svc.is_acceptable(article))

        else:
            with self.assertRaises(exceptions.ArticleNotAcceptable):
                self.svc.is_acceptable(article)

    def test_has_permissions(self):

        journal_source = JournalFixtureFactory.make_journal_source()
        journal1 = Journal(**journal_source)

        publisher_owner_src = AccountFixtureFactory.make_publisher_source()
        publisher_owner = Account(**publisher_owner_src)
        publisher_stranged_src = AccountFixtureFactory.make_publisher_source()
        publisher_stranged = Account(**publisher_stranged_src)
        admin_src = AccountFixtureFactory.make_managing_editor_source()
        admin = Account(**admin_src)

        journal1.set_owner(publisher_owner)
        journal1.save(blocking=True)

        eissn = journal1.bibjson().get_one_identifier("eissn")
        pissn = journal1.bibjson().get_one_identifier("pissn")

        art_source = ArticleFixtureFactory.make_article_source(eissn=eissn,
                                                               pissn=pissn)
        article = Article(**art_source)

        assert self.svc.has_permissions(publisher_stranged, article, False)
        assert self.svc.has_permissions(publisher_owner, article, True)
        assert self.svc.has_permissions(admin, article, True)
        failed_result = self.svc.has_permissions(publisher_stranged, article, True)
        assert failed_result["success"] == 0
        assert failed_result["fail"] == 1
        assert failed_result["update"] == 0
        assert failed_result["new"] == 0
        assert len(failed_result["shared"]) == 0
        assert len(failed_result["unmatched"]) == 0
        assert failed_result["unowned"].sort() == [pissn, eissn].sort()
        # assert failed_result == {'success': 0, 'fail': 1, 'update': 0, 'new': 0, 'shared': [],
        #                          'unowned': [pissn, eissn],
        #                          'unmatched': []}, "received: {}".format(failed_result)