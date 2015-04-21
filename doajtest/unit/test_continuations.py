from doajtest.helpers import DoajTestCase
from portality import models

class TestContinuations(DoajTestCase):

    def setUp(self):
        super(TestContinuations, self).setUp()

    def tearDown(self):
        super(TestContinuations, self).tearDown()

    def test_01_make_history(self):
        # make a journal that is a continuation
        j = models.Journal()
        bibjson = j.bibjson()
        bibjson.title = "An example Journal"
        bibjson.add_identifier(bibjson.E_ISSN, "1234-5678")
        j.make_continuation(isreplacedby="9876-5432")
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
        j.make_continuation(isreplacedby="9876-5432")
        bibjson.remove_identifiers(bibjson.E_ISSN)
        bibjson.add_identifier(bibjson.E_ISSN, "9876-5432")
        bibjson.title = "An updated journal"

        # check there is a history to remove
        history = j.history()
        assert len(history) == 1

        # delete the continuation
        j.remove_history("1234-5678")

        # check that it is gone
        history = j.history()
        assert len(history) == 0

    def test_03_get_history(self):
        # make a journal that is a continuation
        j = models.Journal()
        bibjson = j.bibjson()
        bibjson.title = "An example Journal"
        bibjson.add_identifier(bibjson.E_ISSN, "1234-5678")
        j.make_continuation(isreplacedby="9876-5432")
        bibjson.remove_identifiers(bibjson.E_ISSN)
        bibjson.add_identifier(bibjson.E_ISSN, "9876-5432")
        bibjson.title = "An updated journal"

        old = j.get_history_for("1234-5678")
        assert old.title == "An example Journal"

    def test_04_remove_wrong_history(self):
        # make a journal that is a continuation
        j = models.Journal()
        bibjson = j.bibjson()
        bibjson.title = "An example Journal"
        bibjson.add_identifier(bibjson.E_ISSN, "1234-5678")
        j.make_continuation(isreplacedby="9876-5432")
        bibjson.remove_identifiers(bibjson.E_ISSN)
        bibjson.add_identifier(bibjson.E_ISSN, "9876-5432")
        bibjson.title = "An updated journal"

        # check there is a history
        history = j.history()
        assert len(history) == 1

        # delete the (wrong) continuation
        j.remove_history("7564-0912")

        # check the history is unchanged
        history = j.history()
        assert len(history) == 1

    def test_05_ordered_history(self):
        # make a journal that has several continuations
        j = models.Journal()
        bibjson = j.bibjson()
        bibjson.title = "An example Journal"
        bibjson.add_identifier(bibjson.E_ISSN, "1234-5678")
        j.make_continuation(isreplacedby="9876-5432")

        bibjson.remove_identifiers(bibjson.E_ISSN)
        bibjson.add_identifier(bibjson.E_ISSN, "9876-5432")
        bibjson.title = "An updated journal"
        j.make_continuation(isreplacedby="5432-9876")

        bibjson.remove_identifiers(bibjson.E_ISSN)
        bibjson.add_identifier(bibjson.P_ISSN, "5432-9876")
        bibjson.add_identifier(bibjson.E_ISSN, "5432-987X")
        bibjson.title = "Another Update"
        j.make_continuation(isreplacedby="ABCD-EFGX")

        bibjson.remove_identifiers(bibjson.E_ISSN)
        bibjson.remove_identifiers(bibjson.P_ISSN)
        bibjson.add_identifier(bibjson.P_ISSN, "ABCD-EFGX")
        bibjson.add_identifier(bibjson.E_ISSN, "XXXX-XXXX")
        bibjson.title = "Final Update"

        history = j.history()
        assert len(history) == 3
        assert history[0][3].title == "Another Update"
        assert history[1][3].title == "An updated journal"
        assert history[2][3].title == "An example Journal"

    def test_06_history_around(self):
        # make a journal that has several continuations
        j = models.Journal()
        bibjson = j.bibjson()
        bibjson.title = "An example Journal"
        bibjson.add_identifier(bibjson.E_ISSN, "1234-5678")
        j.make_continuation(isreplacedby="9876-5432")

        bibjson.remove_identifiers(bibjson.E_ISSN)
        bibjson.add_identifier(bibjson.E_ISSN, "9876-5432")
        bibjson.title = "An updated journal"
        j.make_continuation(isreplacedby="5432-9876")

        bibjson.remove_identifiers(bibjson.E_ISSN)
        bibjson.add_identifier(bibjson.P_ISSN, "5432-9876")
        bibjson.add_identifier(bibjson.E_ISSN, "5432-987X")
        bibjson.title = "Another Update"
        j.make_continuation(isreplacedby="ABCD-EFGX")

        bibjson.remove_identifiers(bibjson.E_ISSN)
        bibjson.remove_identifiers(bibjson.P_ISSN)
        bibjson.add_identifier(bibjson.P_ISSN, "ABCD-EFGX")
        bibjson.add_identifier(bibjson.E_ISSN, "XXXX-XXXX")
        bibjson.title = "Final Update"

        # try a few history around calls to check we are getting the right answers

        # first, history around the current journal
        future, past = j.get_history_around("XXXX-XXXX")
        assert len(future) == 0
        assert len(past) == 3
        assert past[0].title == "Another Update"
        assert past[1].title == "An updated journal"
        assert past[2].title == "An example Journal"

        # now in the mid-point
        future, past = j.get_history_around("9876-5432")
        assert len(future) == 2
        assert len(past) == 1
        assert future[0].title == "Final Update"
        assert future[1].title == "Another Update"
        assert past[0].title == "An example Journal"

        # and finally the oldest
        future, past = j.get_history_around("1234-5678")
        assert len(future) == 3
        assert len(past) == 0
        assert future[0].title == "Final Update"
        assert future[1].title == "Another Update"
        assert future[2].title == "An updated journal"
