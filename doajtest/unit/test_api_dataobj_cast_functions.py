from doajtest.helpers import DoajTestCase
from portality.api.v1.data_objects import OutgoingJournal


class TestAPIDataObjCastFunctions(DoajTestCase):

    # we aren't going to talk to ES so override setup and teardown of index
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_01_to_url(self):
        do = OutgoingJournal.from_model(self.jm)
        assert do.bibjson.author_copyright.url == '', do.bibjson.author_copyright.url
        assert do.bibjson.author_copyright.copyright == 'False', do.bibjson.author_copyright.copyright