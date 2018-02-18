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
        self.sugg.save()

        # update request tests
        self.j_old_cd_old_reapp = models.Journal(created_date="2012-06-28T11:26:42Z")
        self.j_old_cd_old_reapp.add_related_application("123456789", date_accepted="2012-07-28T11:26:42Z")
        self.j_old_cd_old_reapp.set_in_doaj(True)
        self.j_old_cd_old_reapp.save()

        self.j_old_cd_new_reapp = models.Journal(created_date="2012-06-28T11:26:42Z")
        self.j_old_cd_new_reapp.add_related_application("123456789", date_accepted="2015-01-01T11:26:42Z")
        self.j_old_cd_new_reapp.set_in_doaj(True)
        self.j_old_cd_new_reapp.save()

        self.j_old_cd_new_reapp_out = models.Journal(created_date="2012-06-28T11:26:42Z")
        self.j_old_cd_new_reapp_out.add_related_application("123456789", date_accepted="2015-01-01T11:26:42Z")
        self.j_old_cd_new_reapp_out.set_in_doaj(False)
        self.j_old_cd_new_reapp_out.save()

        # Refresh the type to force changes in the index, then wait for it to be done
        models.Journal.refresh()
        models.Suggestion.refresh()
        time.sleep(2)

    def tearDown(self):
        super(TestTick, self).tearDown()

    def test_01_tick(self):

        assert self.j_correct.is_ticked()
        assert not self.j_not_in_doaj_excplicit.is_ticked()
        assert not self.j_not_in_doaj_implicit.is_ticked()
        assert not self.j_too_old.is_ticked()
        assert not self.j_too_old_not_in.is_ticked()
        assert not self.j_old_cd_old_reapp.is_ticked()
        assert self.j_old_cd_new_reapp.is_ticked()
        assert not self.j_old_cd_new_reapp_out.is_ticked()
