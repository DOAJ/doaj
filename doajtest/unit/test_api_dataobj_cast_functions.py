from doajtest.helpers import DoajTestCase
from portality.api.v1.data_objects import OutgoingJournal
from portality import models
from doajtest.fixtures.journals import JournalFixtureFactory


class TestAPIDataObjCastFunctions(DoajTestCase):

    # we aren't going to talk to ES so override setup and teardown of index
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_01_to_url(self):
        empty_url_journal_source = JournalFixtureFactory.make_journal_source()
        empty_url_journal_source['bibjson']['copyright']['author_retains'] = False
        empty_url_journal_source['bibjson']['copyright']['url'] = ''
        jm = models.Journal(**empty_url_journal_source)

        do = OutgoingJournal.from_model(jm)
        assert do.bibjson.author_copyright.url == '', do.bibjson.author_copyright.url
        assert do.bibjson.author_copyright.copyright == 'False', do.bibjson.author_copyright.copyright