"""
Unit tests for the EPMC plugin
"""

from unittest import TestCase
from doajtest.fixtures.harvester import EPMCFixtureFactory
from portality.harvester.epmc.epmc_harvester import EPMCHarvester

class TestEPMC(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_01_crosswalk(self):
        md = EPMCFixtureFactory.epmc_metadata()
        h = EPMCHarvester()
        article = h.crosswalk(md)

        assert article.bibjson.title == "A map of human genome variation from population-scale sequencing."
        assert article.get_identifier("doi") == "10.1038/nature09534"
        assert article.get_identifier("pissn") == "0028-0836"
        assert article.get_identifier("eissn") == "1476-4687"
        assert article.bibjson.journal.volume == "467"
        assert article.bibjson.journal.number == "7319"
        assert article.bibjson.journal.title == "Nature"
        assert article.bibjson.journal.language == ["eng"]
        assert article.bibjson.year == "2010"
        assert article.bibjson.month == "10"
        assert article.bibjson.journal.start_page == "1061"
        assert article.bibjson.journal.end_page == "1073"
        assert article.get_link("fulltext") == "http://europepmc.org/articles/PMC3042601?pdf=render"
        assert article.bibjson.abstract.startswith("The 1000 Genomes Project aims to provide")
        assert len(article.bibjson.author) == 6

        assert article.is_api_valid()

        # now just check that an empty document also works
        md = EPMCFixtureFactory.epmc_empty_metadata()
        article = h.crosswalk(md)

        assert article.bibjson.title is None