from doajtest.helpers import DoajTestCase
from portality import models

class TestClient(DoajTestCase):
    def setUp(self):
        super(TestClient, self).setUp()

    def tearDown(self):
        super(TestClient, self).tearDown()

    def test_01_row(self):
        j = models.Journal()
        b = j.bibjson()

        b.title = "My Title"
        b.alternative_title = "Alt Title"
        b.add_url("http://home.com", "homepage")
        b.add_url("http://other.com", "other")
        b.publisher = "Journal House"
        b.add_language("en")
        b.add_language("fr")
        b.add_identifier(b.P_ISSN, "1234-5678")
        b.add_identifier(b.E_ISSN, "9876-5432")
        b.add_keyword("one")
        b.add_keyword("two")
        b.set_oa_start("2004")
        b.set_oa_end("2007")
        b.add_subject("LCC", "Medicine")
        b.country = "GB"
        b.set_license("CC BY", "CC BY")

        j.set_in_doaj(True)
        j.prep()

        row = j.csv()

        assert len(row) == 17
        assert row[0] == "My Title"
        assert row[1] == "Alt Title"
        assert row[2] == "http://home.com", row[2]
        assert row[3] == "Journal House"
        assert row[4] in ["en,fr", "fr,en"]
        assert row[5] == "1234-5678"
        assert row[6] == "9876-5432"
        assert row[7] in ["one,two", "two,one"]
        assert row[8] == "2004"
        assert row[9] == "2007"
        # assert row[10] is not None and row[10] != "", row[10] # created_date, only set on save()
        assert row[11] == "Medicine"
        assert row[12] == "United Kingdom", row[12]
        assert row[13] == ""
        assert row[14] == ""
        assert row[15] == "BY"
        assert row[16] == "Yes"
