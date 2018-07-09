from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets

from doajtest.fixtures import ArticleFixtureFactory, JournalFixtureFactory, AccountFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.models import Article, Journal, Account
from portality.lib.paths import rel2abs
from doajtest.mocks.bll_article import BLLArticleMockFactory
from datetime import datetime

def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "article_get_duplicates"), "get_duplicates", "test_id", {"test_id" : []})


EXCEPTIONS = {
    "ArgumentException" : exceptions.ArgumentException
}

class TestBLLArticleGetDuplicates(DoajTestCase):

    def setUp(self):
        super(TestBLLArticleGetDuplicates, self).setUp()
        self.svc = DOAJ.articleService()
        self._old_discover_duplicates = self.svc.discover_duplicates

    def tearDown(self):
        self.svc.discover_duplicates = self._old_discover_duplicates
        super(TestBLLArticleGetDuplicates, self).tearDown()

    @parameterized.expand(load_cases)
    def test_01_get_duplicates(self, name, kwargs):

        article_arg = kwargs.get("article")
        owner_arg = kwargs.get("owner")
        doi_duplicates_arg = kwargs.get("doi_duplicates")
        fulltext_duplicates_arg = kwargs.get("fulltext_duplicates")
        overlap_arg = kwargs.get("overlap")
        raises_arg = kwargs.get("raises")

        raises = EXCEPTIONS.get(raises_arg)

        doi_duplicates = -1
        if doi_duplicates_arg not in ["-"]:
            doi_duplicates = int(doi_duplicates_arg)

        fulltext_duplicates = -1
        if fulltext_duplicates_arg not in ["-"]:
            fulltext_duplicates = int(fulltext_duplicates_arg)

        overlap = -1
        if overlap_arg not in ["-"]:
            overlap = int(overlap_arg)

        expected_count = doi_duplicates + fulltext_duplicates - overlap

        ###############################################
        ## set up

        owner = None
        if owner_arg != "no":
            owner = Account(**AccountFixtureFactory.make_publisher_source())

        owner_id = None
        if owner is not None:
            owner_id = owner.id

        # generate our incoming article
        article = None
        if article_arg == "yes":
            source = ArticleFixtureFactory.make_article_source()
            article = Article(**source)
            article.set_id()

        mock = BLLArticleMockFactory.discover_duplicates(doi_duplicates, fulltext_duplicates, overlap)
        self.svc.discover_duplicates = mock

        ###########################################################
        # Execution

        first_article = None

        # first do get_duplicates
        if raises is not None:
            with self.assertRaises(raises):
                self.svc.get_duplicates(article, owner_id)
        else:
            duplicates = self.svc.get_duplicates(article, owner_id)

            if len(duplicates) > 0:
                first_article = duplicates[0]

            # check that we have the number of results we expected
            assert len(duplicates) == expected_count

            # check that the articles are unique in the list
            article_ids = [a.id for a in duplicates]
            article_ids.sort()
            deduped = list(set(article_ids))
            deduped.sort()  # so it's comparable to the article_ids list, as the set() call destroys ordering
            assert article_ids == deduped   # i.e. that there were no duplicates

            # check that the articles are ordered by last_updated
            last_updateds = [datetime.strptime(a.last_updated, "%Y-%m-%dT%H:%M:%SZ") for a in duplicates]
            sorted_lu = sorted(last_updateds, reverse=True)
            assert sorted_lu == last_updateds   # i.e. they were already sorted

        # then the same again on the singular get_duplicate
        if raises is not None:
            with self.assertRaises(raises):
                self.svc.get_duplicate(article, owner_id)
        else:
            duplicate = self.svc.get_duplicate(article, owner_id)

            if expected_count > 0:
                assert isinstance(duplicate, Article)
                assert duplicate.id == first_article.id
            else:
                assert duplicate is None

