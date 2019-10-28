"""
Unit tests for the DOAJ client
"""

from unittest import TestCase
from doajtest.fixtures.journals import JournalFixtureFactory
from portality.api.v1.client import models


class TestDOAJ(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_01_journal_issns(self):
        source = JournalFixtureFactory.make_journal_source()
        j = models.Journal(source)
        issns = j.all_issns()
        assert "1234-5678" in issns
        assert "9876-5432" in issns
        assert len(issns) == 2

    def test_02_validate_article(self):
        invalid = {"bibjson": {}}

        # then check that the api validation method works
        a = models.Article(invalid)
        assert not a.is_api_valid()
