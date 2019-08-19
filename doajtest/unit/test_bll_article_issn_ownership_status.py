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
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "article_issn_ownership_status"), "issn_ownership_status", "test_id",
                               {"test_id" : []})


EXCEPTIONS = {
    "ArgumentException" : exceptions.ArgumentException
}

class TestBLLArticleISSNOwnershipStatus(DoajTestCase):

    def setUp(self):
        super(TestBLLArticleISSNOwnershipStatus, self).setUp()
        self._old_find_by_issn = Journal.find_by_issn

    def tearDown(self):
        Journal.find_by_issn = self._old_find_by_issn
        super(TestBLLArticleISSNOwnershipStatus, self).tearDown()

    @parameterized.expand(load_cases)
    def test_01_issn_ownership_status(self, name, kwargs):

        article_arg = kwargs.get("article")
        owner_arg = kwargs.get("owner")
        article_eissn_arg = kwargs.get("article_eissn")
        article_pissn_arg = kwargs.get("article_pissn")
        seen_eissn_arg = kwargs.get("seen_eissn")
        seen_pissn_arg = kwargs.get("seen_pissn")
        journal_owner_arg = kwargs.get("journal_owner")

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

        issns = []
        if eissn is not None and pissn is not None and seen_eissn_arg == "yes" and seen_pissn_arg == "yes":
            issns.append((eissn, pissn))
        if eissn is not None and seen_eissn_arg == "yes":
            issns.append((eissn, "4321-9876"))
            issns.append((eissn, None))
        if pissn is not None and seen_pissn_arg == "yes":
            issns.append(("6789-4321", pissn))
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
                svc.issn_ownership_status(article, owner_id)
        else:
            owned, shared, unowned, unmatched = svc.issn_ownership_status(article, owner_id)

            owned_count = 0
            if seen_eissn_arg == "yes" and eissn is not None and journal_owner_arg in ["correct"]:
                assert eissn in owned
                owned_count += 1
            elif eissn is not None:
                assert eissn not in owned

            if seen_pissn_arg == "yes" and pissn is not None and journal_owner_arg in ["correct"]:
                assert pissn in owned
                owned_count += 1
            elif pissn is not None:
                assert pissn not in owned

            assert len(owned) == owned_count


            shared_count = 0
            if seen_eissn_arg == "yes" and eissn is not None and journal_owner_arg in ["mix"]:
                assert eissn in shared
                shared_count += 1
            elif eissn is not None:
                assert eissn not in shared

            if seen_pissn_arg == "yes" and pissn is not None and journal_owner_arg in ["mix"]:
                assert pissn in shared
                shared_count += 1
            elif pissn is not None:
                assert pissn not in shared

            assert len(shared) == shared_count


            unowned_count = 0
            if seen_eissn_arg == "yes" and eissn is not None and journal_owner_arg in ["incorrect", "none"]:
                assert eissn in unowned
                unowned_count += 1
            elif eissn is not None:
                assert eissn not in unowned

            if seen_pissn_arg == "yes" and pissn is not None and journal_owner_arg in ["incorrect", "none"]:
                assert pissn in unowned
                unowned_count += 1
            elif pissn is not None:
                assert pissn not in unowned

            assert len(unowned) == unowned_count


            unmatched_count = 0
            if seen_eissn_arg == "no" and eissn is not None:
                assert eissn in unmatched
                unmatched_count += 1
            elif eissn is not None:
                assert eissn not in unmatched

            if seen_pissn_arg == "no" and pissn is not None:
                assert pissn in unmatched
                unmatched_count += 1
            elif pissn is not None:
                assert pissn not in unmatched

            assert len(unmatched) == unmatched_count
