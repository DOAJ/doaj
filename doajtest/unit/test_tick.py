import doajtest  # runs the __init__.py which runs the tests bootstrap code. All tests should import this.
from doajtest.helpers import DoajTestCase
from portality import models
import time

class TestTick(DoajTestCase):

    def setUp(self):
        super(TestTick, self).setUp()
        self.j_correct = models.Journal(created_date="2014-06-28T11:26:42Z")
        self.j_correct.set_in_doaj(True)
        self.j_correct.save()

        self.j_not_in_doaj_excplicit = models.Journal(created_date="2014-06-28T11:26:42Z")
        self.j_not_in_doaj_excplicit.set_in_doaj(False)
        self.j_not_in_doaj_excplicit.save()

        self.j_not_in_doaj_implicit = models.Journal(created_date="2014-06-28T11:26:42Z")
        self.j_not_in_doaj_implicit.save()

        self.j_too_old = models.Journal(created_date="2012-06-28T11:26:42Z")
        self.j_too_old.set_in_doaj(True)
        self.j_too_old.save()

        self.j_too_old_not_in = models.Journal(created_date="2012-06-28T11:26:42Z")
        self.j_too_old_not_in.set_in_doaj(False)
        self.j_too_old_not_in.save()

        self.sugg = models.Suggestion(created_date="2014-06-28T11:26:42Z")
        self.sugg.set_in_doaj(True)
        self.sugg.save()

        # Refresh the type to force changes in the index, then wait for it to be done
        models.Journal.refresh()
        models.Suggestion.refresh()
        time.sleep(2)

    def tearDown(self):
        super(TestTick, self).tearDown()

    def test_01_tick(self):
        print self.j_correct.json

        assert self.j_correct.is_ticked()
        assert not self.j_not_in_doaj_excplicit.is_ticked()
        assert not self.j_not_in_doaj_implicit.is_ticked()
        assert not self.j_too_old.is_ticked()
        assert not self.j_too_old_not_in.is_ticked()
        assert not self.sugg.is_ticked()
