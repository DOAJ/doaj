from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets

from doajtest.fixtures import ArticleFixtureFactory, JournalFixtureFactory, AccountFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.models import Article, Journal, Account
from portality.lib.paths import rel2abs

def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "article_discover_duplicates"), "discover_duplicates", "test_id", {"test_id" : []})


EXCEPTIONS = {
    "DuplicateArticleException" : exceptions.DuplicateArticleException,
    "ArgumentException" : exceptions.ArgumentException
}

IDENTS = [
    {"doi" : "10.1234/abc/1", "fulltext" : "http://example.com/1"},
    {"doi" : "10.1234/abc/2", "fulltext" : "http://example.com/2"},
    {"doi" : "10.1234/abc/3", "fulltext" : "http://example.com/3"},
    {"doi" : "10.1234/abc/4", "fulltext" : "http://example.com/4"},
    {"doi" : "10.1234/abc/5", "fulltext" : "http://example.com/5"},
    {"doi" : "10.1234/abc/6", "fulltext" : "http://example.com/6"},
    {"doi" : "10.1234/abc/7", "fulltext" : "http://example.com/7"},
    {"doi" : "10.1234/abc/8", "fulltext" : "http://example.com/8"},
    {"doi" : "10.1234/abc/9", "fulltext" : "http://example.com/9"},
    {"doi" : "10.1234/abc/10", "fulltext" : "http://example.com/10"}
]

class TestBLLArticleDiscoverDuplicates(DoajTestCase):

    def setUp(self):
        super(TestBLLArticleDiscoverDuplicates, self).setUp()

    def tearDown(self):
        super(TestBLLArticleDiscoverDuplicates, self).tearDown()

    @parameterized.expand(load_cases)
    def test_01_discover_duplicates(self, name, kwargs):

        article_arg = kwargs.get("article")
        owner_arg = kwargs.get("owner")
        article_issn_arg = kwargs.get("article_issn")
        article_doi_arg = kwargs.get("article_doi")
        doi_duplicate_arg = kwargs.get("doi_duplicate")
        article_fulltext_arg = kwargs.get("article_fulltext")
        fulltext_duplicate_arg = kwargs.get("fulltext_duplicate")
        articles_by_doi_arg = kwargs.get("articles_by_doi")
        articles_by_fulltext_arg = kwargs.get("articles_by_fulltext")
        raises_arg = kwargs.get("raises")

        raises = EXCEPTIONS.get(raises_arg)

        ###############################################
        ## set up

        owner = None
        if owner_arg != "none":
            owner = Account(**AccountFixtureFactory.make_publisher_source())

        owner_id = None
        if owner is not None:
            owner_id = owner.id

        # create a journal for the owner
        if owner_arg not in ["none"]:
            source = JournalFixtureFactory.make_journal_source(in_doaj=True)
            journal = Journal(**source)
            journal.set_owner(owner.id)
            journal.bibjson().remove_identifiers()
            journal.bibjson().add_identifier("eissn", "1234-5678")
            journal.bibjson().add_identifier("pissn", "9876-5432")
            journal.save(blocking=True)

        # determine what we need to load into the index
        article_ids = []
        if owner_arg not in ["none", "no_articles"]:
            for i, ident in enumerate(IDENTS):
                source = ArticleFixtureFactory.make_article_source(eissn="1234-5678", pissn="9876-5432", doi=ident["doi"], fulltext=ident["fulltext"])
                article = Article(**source)
                article.set_id()
                block = i == len(IDENTS) - 1
                article.save(blocking=block)
                article_ids.append(article.id)

        # generate our incoming article
        article = None
        doi = None
        fulltext = None
        if article_arg == "yes":
            eissn = "1234=5678" if article_issn_arg == "matching" else "4321-9876"
            pissn = "9876-5432" if article_issn_arg == "matching" else "6789-1234"

            if article_doi_arg == "yes":
                doi = "10.1234/abc/11"
                if doi_duplicate_arg == "yes":
                    doi = IDENTS[0]["doi"]

            if article_fulltext_arg == "yes":
                fulltext = "http://example.com/11"
                if fulltext_duplicate_arg == "yes":
                    fulltext = IDENTS[0]["fulltext"]

            source = ArticleFixtureFactory.make_article_source(eissn=eissn, pissn=pissn, doi=doi, fulltext=fulltext)
            article = Article(**source)

            # we need to do this if doi or fulltext are none, because the factory will set a default if we don't
            # provide them
            if doi is None:
                article.bibjson().remove_identifiers("doi")
            if fulltext is None:
                article.bibjson().remove_urls("fulltext")

            article.set_id()

        ###########################################################
        # Execution

        svc = DOAJ.articleService()
        if raises is not None:
            with self.assertRaises(raises):
                svc.discover_duplicates(article, owner_id)
        else:
            possible_articles = svc.discover_duplicates(article, owner_id)

            if articles_by_doi_arg == "yes":
                assert "doi" in possible_articles
                assert len(possible_articles["doi"]) == 1
                assert possible_articles["doi"][0].id == article_ids[0]
            else:
                if possible_articles is not None:
                    assert "doi" not in possible_articles

            if articles_by_fulltext_arg == "yes":
                assert "fulltext" in possible_articles
                assert len(possible_articles["fulltext"]) == 1
                assert possible_articles["fulltext"][0].id == article_ids[0]
            else:
                if possible_articles is not None:
                    assert "fulltext" not in possible_articles
