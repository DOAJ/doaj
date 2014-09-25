from unittest import TestCase
from portality import core, dao

import time

class DoajTestCase(TestCase):
    def setUp(self):
        core.initialise_index(core.app)
        time.sleep(1)

    def tearDown(self):
        dao.DomainObject.destroy_index()
        time.sleep(1)