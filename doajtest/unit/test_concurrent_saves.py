from doajtest.helpers import DoajTestCase
from portality.util import patch_config
from doajtest.fixtures import JournalFixtureFactory
from portality.models import Journal
from portality.bll.exceptions import ConcurrentUpdateRequestException
from portality.bll import DOAJ
from portality.core import app
import time


class TestConcurrentSaves(DoajTestCase):
    def setUp(self):
        super(TestConcurrentSaves, self).setUp()
        # Re-enable concurrency check for this test
        self.original_config = patch_config(self.app_test, {"UR_CONCURRENCY_TIMEOUT": 10})

    def tearDown(self):
        super(TestConcurrentSaves, self).tearDown()
        patch_config(self.app_test, self.original_config)

    def test_01_update_request(self):
        # we need a journal to create update requests for
        source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        j = Journal(**source)
        j.save(blocking=True)

        # create two update requests at the same time.  These are our duplicates
        appsvc = DOAJ.applicationService()
        ur1, jl1, al1 = appsvc.update_request_for_journal(j.id)
        ur2, jl2, al2 = appsvc.update_request_for_journal(j.id)

        # save the first update request, this should succeed
        ur1.save()

        # immediately attempt to save the second update request.  This should
        # fail as there is already an UR in the pipeline
        with self.assertRaises(ConcurrentUpdateRequestException):
            ur2.save()

        # wait until the redis key times out, and then try making a 3rd UR
        wait = app.config.get("UR_CONCURRENCY_TIMEOUT", 10) + 1
        time.sleep(wait)
        ur3, jl3, al3 = appsvc.update_request_for_journal(j.id)

        # this third UR should be the same as the first one, as the index is now
        # in a consistent state
        assert ur3.id == ur1.id

        # saving it should work as normal
        ur3.save()
