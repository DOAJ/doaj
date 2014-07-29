from unittest import TestCase
from portality import models

class TestSnapshot(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_01_make_history(self):
        # make a journal that is a continuation
        j = models.Journal()
        bibjson = j.bibjson()
        bibjson.title = "An example Journal"
        bibjson.add_identifier(bibjson.E_ISSN, "1234-5678")
        j.snapshot(isreplacedby="9876-5432")
        bibjson.remove_identifiers(bibjson.E_ISSN)
        bibjson.add_identifier(bibjson.E_ISSN, "9876-5432")
        bibjson.title = "An updated journal"

        # check that the continuation got registered fine
        history = j.history()
        assert len(history) == 1
        for date, replaces, isreplacedby, hbj in history:
            assert replaces is None
            assert len(isreplacedby) == 1
            assert "9876-5432" in isreplacedby
            assert hbj.title == "An example Journal"
            issns = hbj.get_identifiers(hbj.E_ISSN)
            assert len(issns) == 1
            assert "1234-5678" in issns

    def test_02_remove_history(self):
        # make a journal that is a continuation
        j = models.Journal()
        bibjson = j.bibjson()
        bibjson.title = "An example Journal"
        bibjson.add_identifier(bibjson.E_ISSN, "1234-5678")
        j.snapshot(isreplacedby="9876-5432")
        bibjson.remove_identifiers(bibjson.E_ISSN)
        bibjson.add_identifier(bibjson.E_ISSN, "9876-5432")
        bibjson.title = "An updated journal"

        # delete the continuation
        j.remove_history("1234-5678")

        # check that it is cone
        history = j.history()
        assert len(history) == 0

    def test_03_get_history(self):
        # make a journal that is a continuation
        j = models.Journal()
        bibjson = j.bibjson()
        bibjson.title = "An example Journal"
        bibjson.add_identifier(bibjson.E_ISSN, "1234-5678")
        j.snapshot(isreplacedby="9876-5432")
        bibjson.remove_identifiers(bibjson.E_ISSN)
        bibjson.add_identifier(bibjson.E_ISSN, "9876-5432")
        bibjson.title = "An updated journal"

        old = j.get_history_for("1234-5678")
        assert old.title == "An example Journal"