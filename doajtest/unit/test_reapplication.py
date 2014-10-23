from doajtest.helpers import DoajTestCase
from portality import models, reapplication, clcsv
import os

class TestReApplication(DoajTestCase):

    def setUp(self):
        super(TestReApplication, self).setUp()

    def tearDown(self):
        super(TestReApplication, self).tearDown()
        if os.path.exists("reapp.csv") and os.path.isfile("reapp.csv"):
            os.remove("reapp.csv")


    def test_01_make_reapplication(self):
        # first make ourselves a journal with the key ingredients
        j = models.Journal()
        bj = j.bibjson()
        bj.title = "Journal Title"                      # some bibjson
        j.set_application_status("accepted")            # an application status of accepted
        j.add_note("An important note")                 # a note
        j.add_contact("Contact", "contact@email.com")   # contact details
        j.set_owner("theowner")                         # journal owner account
        j.set_editor_group("editorgroup")               # editorial group
        j.set_editor("associate")                       # assigned associate editor

        # save it so that it acquires an id, created_date, last_updated and an index record
        j.save()
        j.refresh()

        # now call to make the reapplication
        reapp = j.make_reapplication()
        rbj = reapp.bibjson()

        # now check that the reapplication has the properties we'd expect
        assert rbj.title == "Journal Title"
        assert reapp.id != j.id
        assert reapp.suggested_on is not None
        assert reapp.application_status == "reapplication"
        assert len(reapp.notes()) == 1
        assert len(reapp.contacts()) == 1
        assert reapp.owner == "theowner"
        assert reapp.editor_group == "editorgroup"
        assert reapp.editor == "associate"
        assert reapp.current_journal == j.id
        assert j.current_application == reapp.id
        assert reapp.created_date is not None
        assert reapp.last_updated is not None

    def test_02_make_csv_vbasic(self):
        s1 = models.Suggestion()
        bj1 = s1.bibjson()
        bj1.title = "The Title"
        bj1.add_identifier("eissn", "1245-5678")

        s2 = models.Suggestion()
        bj2 = s2.bibjson()
        bj2.title = "Second One"
        bj2.add_identifier("pissn", "9876-5432")

        reapplication.make_csv("reapp.csv", [s1, s2])

        assert os.path.exists("reapp.csv")

        sheet = clcsv.ClCsv("reapp.csv")

