from doajtest.fixtures import ArticleFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.models import Article


class TestDOICaseNormalisation(DoajTestCase):

    def test_01_add_identifier_lower_cases_doi(self):
        # DOIs added via the bibjson API should always be stored lower case
        a = Article()
        bj = a.bibjson()
        bj.add_identifier(bj.DOI, "10.1234/UPPER-Case")

        assert bj.get_one_identifier(bj.DOI) == "10.1234/upper-case"

    def test_02_raw_construction_normalised_on_save(self):
        # Articles built directly from a raw dict (e.g. from an API payload) bypass
        # add_identifier, so the identifier's case should still be corrected when the
        # article's index is generated (on prep/save)
        source = ArticleFixtureFactory.make_article_source(
            pissn="1111-1111", eissn="2222-2222", doi="10.5555/MixedCase-DOI"
        )
        a = Article(**source)

        # before prep/save, the raw (mixed case) value is still present
        assert a.bibjson().get_one_identifier(a.bibjson().DOI) == "10.5555/MixedCase-DOI"

        a.prep()

        assert a.bibjson().get_one_identifier(a.bibjson().DOI) == "10.5555/mixedcase-doi"
        assert a.data["index"]["doi"] == "10.5555/mixedcase-doi"

    def test_03_get_normalised_doi_lower_case(self):
        source = ArticleFixtureFactory.make_article_source(
            pissn="1111-1111", eissn="2222-2222", doi="10.5555/AnotherOne"
        )
        a = Article(**source)
        assert a.get_normalised_doi() == "10.5555/anotherone"
