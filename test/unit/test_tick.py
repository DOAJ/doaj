from unittest import TestCase
from portality import models
import uuid, time
import logging
from portality.core import app

app.logger.setLevel(logging.WARNING)

requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

object_list = []

class TestSnapshot(TestCase):

    def setUp(self):

        self.j_correct = models.Journal(created_date="2014-06-28T11:26:42Z")
        self.j_correct.set_in_doaj(True)
        self.j_correct.save()
        object_list.append(self.j_correct)

        self.j_not_in_doaj_excplicit = models.Journal(created_date="2014-06-28T11:26:42Z")
        self.j_not_in_doaj_excplicit.set_in_doaj(False)
        self.j_not_in_doaj_excplicit.save()
        object_list.append(self.j_not_in_doaj_excplicit)

        self.j_not_in_doaj_implicit = models.Journal(created_date="2014-06-28T11:26:42Z")
        self.j_not_in_doaj_implicit.save()
        object_list.append(self.j_not_in_doaj_implicit)
        
        self.j_too_old = models.Journal(created_date="2012-06-28T11:26:42Z")
        self.j_too_old.set_in_doaj(True)
        self.j_too_old.save()
        object_list.append(self.j_too_old)

        self.j_too_old_not_in = models.Journal(created_date="2012-06-28T11:26:42Z")
        self.j_too_old_not_in.set_in_doaj(False)
        self.j_too_old_not_in.save()
        object_list.append(self.j_too_old_not_in)
        
        self.sugg = models.Suggestion(created_date="2014-06-28T11:26:42Z")
        self.sugg.set_in_doaj(True)
        self.sugg.save()
        object_list.append(self.sugg)

        # Refresh the type to force changes in the index, then wait for it to be done
        models.Journal.refresh()
        models.Suggestion.refresh()
        time.sleep(2)
        
    def tearDown(self):    
        for obj in object_list:
            obj.delete()

    def test_01_tick(self):
        print self.j_correct.json

        assert self.j_correct.is_ticked()
        assert not self.j_not_in_doaj_excplicit.is_ticked()
        assert not self.j_not_in_doaj_implicit.is_ticked()
        assert not self.j_too_old.is_ticked()
        assert not self.j_too_old_not_in.is_ticked()
        assert not self.sugg.is_ticked()
