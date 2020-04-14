from doajtest.helpers import DoajTestCase
from portality.api.v2.data_objects.journal import OutgoingJournal
from portality import models
from doajtest.fixtures.v2.journals import JournalFixtureFactory


class TestAPIDataObjCastFunctions(DoajTestCase):

    # we aren't going to talk to ES so override setup and teardown of index
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_01_to_url(self):
        empty_url_journal_source = JournalFixtureFactory.make_journal_source()
        print(empty_url_journal_source['bibjson'])
        empty_url_journal_source['bibjson']['copyright']['url'] = ''
        jm = models.Journal(**empty_url_journal_source)

        do = OutgoingJournal.from_model(jm)
        copyright = do.data["bibjson"]["copyright"]
        assert "url" not in copyright
        assert copyright["author_retains"] == False, copyright["author_retains"]