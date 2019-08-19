from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets

from doajtest.fixtures import DoajXmlArticleFixtureFactory, JournalFixtureFactory, AccountFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.models import Article, Journal, Account
from portality.lib.paths import rel2abs

def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "article_discover_duplicates"), "discover_duplicates", "test_id",
                               {"test_id" : []})


EXCEPTIONS = {
    "DuplicateArticleException" : exceptions.DuplicateArticleException,
    "ArgumentException" : exceptions.ArgumentException,
    "ValueError" : ValueError
}

IDENTS = [
    {"doi" : "10.1234/abc/1", "fulltext" : "//example.com/1"},
    {"doi" : "10.1234/abc/2", "fulltext" : "//example.com/2"},
    {"doi" : "10.1234/abc/3", "fulltext" : "//example.com/3"},
    {"doi" : "10.1234/abc/4", "fulltext" : "//example.com/4"},
    {"doi" : "10.1234/abc/5", "fulltext" : "//example.com/5"},
    {"doi" : "10.1234/abc/6", "fulltext" : "//example.com/6"},
    {"doi" : "10.1234/abc/7", "fulltext" : "//example.com/7"},
    {"doi" : "10.1234/abc/8", "fulltext" : "//example.com/8"},
    {"doi" : "10.1234/abc/9", "fulltext" : "//example.com/9"},
    {"doi" : "10.1234/abc/10", "fulltext" : "//example.com/10"},
    {"doi" : "this isn't a doi", "fulltext" : "this isn't a fulltext url"}
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
        aids_block = []
        if owner_arg not in ["none", "no_articles"]:
            for i, ident in enumerate(IDENTS):
                the_doi = ident["doi"]
                if doi_duplicate_arg == "padded":
                    the_doi = "  " + the_doi + "  "
                elif doi_duplicate_arg == "prefixed":
                    the_doi = "https://dx.doi.org/" + the_doi

                the_fulltext = ident["fulltext"]
                if article_fulltext_arg != "invalid":
                    if fulltext_duplicate_arg == "padded":
                        the_fulltext = "  http:" + the_fulltext
                    elif fulltext_duplicate_arg == "http":
                        the_fulltext = "http:" + the_fulltext
                    elif fulltext_duplicate_arg == "https":
                        the_fulltext = "https:" + the_fulltext
                    else:
                        the_fulltext = "http:" + the_fulltext

                source = DoajXmlArticleFixtureFactory.make_article_source(eissn="1234-5678", pissn="9876-5432", doi=the_doi, fulltext=the_fulltext)
                article = Article(**source)
                article.set_id()
                article.save()
                article_ids.append(article.id)
                aids_block.append((article.id, article.last_updated))

        # generate our incoming article
        article = None
        doi = None
        fulltext = None
        if article_arg == "yes":
            eissn = "1234=5678" # one matching
            pissn = "6789-1234" # the other not - issn matches are not relevant to this test

            if article_doi_arg in ["yes", "padded"]:
                doi = "10.1234/abc/11"
                if doi_duplicate_arg in ["yes", "padded"]:
                    doi = IDENTS[0]["doi"]
                if article_doi_arg == "padded":
                    doi = "  doi:" + doi + "  "
            elif article_doi_arg in ["invalid"]:
                doi = IDENTS[-1]["doi"]

            if article_fulltext_arg in ["yes", "padded", "https"]:
                fulltext = "//example.com/11"
                if fulltext_duplicate_arg in ["yes", "padded", "https"]:
                    fulltext = IDENTS[0]["fulltext"]
                if fulltext_duplicate_arg == "padded":
                    fulltext = "  http:" + fulltext + "  "
                elif fulltext_duplicate_arg == "https":
                    fulltext = "https:" + fulltext
                else:
                    fulltext = "http:" + fulltext
            elif article_fulltext_arg == "invalid":
                fulltext = IDENTS[-1]["fulltext"]

            source = DoajXmlArticleFixtureFactory.make_article_source(eissn=eissn, pissn=pissn, doi=doi, fulltext=fulltext)
            article = Article(**source)

            # we need to do this if doi or fulltext are none, because the factory will set a default if we don't
            # provide them
            if doi is None:
                article.bibjson().remove_identifiers("doi")
            if fulltext is None:
                article.bibjson().remove_urls("fulltext")

            article.set_id()

        Article.blockall(aids_block)

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
                # if this is the "invalid" doi, then we expect it to match the final article, otherwise match the first
                if article_doi_arg == "invalid":
                    assert possible_articles["doi"][0].id == article_ids[-1]
                else:
                    assert possible_articles["doi"][0].id == article_ids[0]
            else:
                if possible_articles is not None:
                    assert "doi" not in possible_articles

            if articles_by_fulltext_arg == "yes":
                assert "fulltext" in possible_articles
                assert len(possible_articles["fulltext"]) == 1
                # if this is the "invalid" fulltext url, then we expect it to match the final article, otherwise match the first
                if article_fulltext_arg == "invalid":
                    assert possible_articles["fulltext"][0].id == article_ids[-1]
                else:
                    assert possible_articles["fulltext"][0].id == article_ids[0]
            else:
                if possible_articles is not None:
                    assert "fulltext" not in possible_articles
