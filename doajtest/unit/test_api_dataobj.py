from doajtest.helpers import DoajTestCase
from portality.lib.dataobj import DataObj
from portality.api.v1.data_objects import JournalDO
from portality import models
from datetime import datetime
from doajtest.fixtures import ApplicationFixtureFactory, JournalFixtureFactory, ArticleFixtureFactory
import time

class TestClient(DoajTestCase):

    # we aren't going to talk to ES so override setup and teardown of index
    def setUp(self):
        self.jm = models.Journal(**JournalFixtureFactory.make_journal_source())

    def tearDown(self):
        pass

    def test_01_create_empty(self):
        """Create an empty dataobject, mostly to check it doesn't die a recursive death"""
        do = DataObj(raw={}, _type='test')
        assert do._type == 'test'
        assert do._data == {}
        assert do._struct == {}

    def test_02_create_from_dict(self):
        expected_struct = JournalFixtureFactory.make_journal_apido_struct()
        do = DataObj(raw=self.jm.data, _struct=expected_struct, _type='journal', _silent_drop_extra_fields=True)
        assert do._type == 'journal'
        #assert do._data == {}
        assert do._struct == expected_struct

    def test_03_create_from_model(self):
        expected_struct = JournalFixtureFactory.make_journal_apido_struct()
        do = JournalDO.from_model(self.jm)
        assert do._type == 'journal'
        #assert do._data == {}
        assert do._struct == expected_struct