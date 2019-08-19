from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets

from doajtest.fixtures import DoajXmlArticleFixtureFactory, AccountFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.models import Article, Journal, Account
from portality.lib.paths import rel2abs
from doajtest.mocks.model_Journal import ModelJournalMockFactory

def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "article_is_legitimate_owner"), "is_legitimate_owner", "test_id",
                               {"test_id" : []})


EXCEPTIONS = {
    "ArgumentException" : exceptions.ArgumentException
}

class TestBLLArticleIsLegitimateOwner(DoajTestCase):

    def setUp(self):
        super(TestBLLArticleIsLegitimateOwner, self).setUp()
        self._old_find_by_issn = Journal.find_by_issn

    def tearDown(self):
        Journal.find_by_issn = self._old_find_by_issn
        super(TestBLLArticleIsLegitimateOwner, self).tearDown()

    @parameterized.expand(load_cases)
    def test_01_is_legitimate_owner(self, name, kwargs):

        article_arg = kwargs.get("article")
        owner_arg = kwargs.get("owner")
        article_eissn_arg = kwargs.get("article_eissn")
        article_pissn_arg = kwargs.get("article_pissn")
        seen_eissn_arg = kwargs.get("seen_eissn")
        seen_pissn_arg = kwargs.get("seen_pissn")
        journal_owner_arg = kwargs.get("journal_owner")

        raises_arg = kwargs.get("raises")
        legit_arg = kwargs.get("legit")

        raises = EXCEPTIONS.get(raises_arg)

        ###############################################
        ## set up

        owner = None
        if owner_arg != "none":
            owner = Account(**AccountFixtureFactory.make_publisher_source())

        owner_id = None
        if owner is not None:
            owner_id = owner.id

        # generate our incoming article
        article = None
        eissn = None
        pissn = None
        if article_arg == "exists":
            source = DoajXmlArticleFixtureFactory.make_article_source()
            article = Article(**source)
            article.set_id()

            article.bibjson().remove_identifiers("pissn")
            if article_pissn_arg == "yes":
                pissn = "1234-5678"
                article.bibjson().add_identifier("pissn", pissn)

            article.bibjson().remove_identifiers("eissn")
            if article_eissn_arg == "yes":
                eissn = "9876-5432"
                article.bibjson().add_identifier("eissn", eissn)

        # assemble the issns that will appear to be in the index.  One that is irrelevant, and just
        # serves to be "noise" in the database, and the other that matches the spec required by
        # the test
        issns = [("1111-1111", "2222-2222")]
        if eissn is not None and pissn is not None and seen_eissn_arg == "yes" and seen_pissn_arg == "yes":
            issns.append((eissn, pissn))
        if eissn is not None and seen_eissn_arg == "yes":
            issns.append((eissn, None))
        if pissn is not None and seen_pissn_arg == "yes":
            issns.append((None, pissn))

        owners = []
        if journal_owner_arg == "none":
            owners = [None]
        elif journal_owner_arg == "correct" and owner_id is not None:
            owners = [owner_id]
        elif journal_owner_arg == "incorrect":
            owners = ["randomowner"]
        elif journal_owner_arg == "mix" and owner_id is not None:
            owners.append(owner_id)
            owners.append("randomowner")
            owners.append(None)

        mock = ModelJournalMockFactory.find_by_issn(issns, owners)
        Journal.find_by_issn = mock

        ###########################################################
        # Execution

        svc = DOAJ.articleService()

        if raises is not None:
            with self.assertRaises(raises):
                svc.is_legitimate_owner(article, owner_id)
        else:
            legit = svc.is_legitimate_owner(article, owner_id)

            if legit_arg == "no":
                assert legit is False
            elif legit_arg == "yes":
                assert legit is True
