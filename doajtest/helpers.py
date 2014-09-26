from unittest import TestCase
from portality import core, dao
from doajtest.bootstrap import prepare_for_test
import time

prepare_for_test()

class DoajTestCase(TestCase):
    def setUp(self):
        core.initialise_index(core.app)
        time.sleep(1)

    def tearDown(self):
        dao.DomainObject.destroy_index()
        time.sleep(1)