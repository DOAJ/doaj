"""
Unit tests for the Harvest State mechanics
"""

from doajtest.helpers import DoajTestCase
from doajtest.fixtures.harvester import HarvestStateFactory
from portality.models import harvester as models
from portality.harvester import workflow
from portality.core import app
from portality.lib import plugin, dates

# from service.tests import fixtures
# from service import models, workflow
# import time
#from octopus.core import app
#from octopus.lib import plugin, dates

class TestState(DoajTestCase):
    def setUp(self):
        super(TestState, self).setUp()

    def tearDown(self):
        super(TestState, self).tearDown()

    def test_01_harvest_state_do(self):
        # make one blank and play with its methods
        hs = models.HarvestState()
        hs.account = "abcdefg"
        hs.issn = "9876-5432"
        hs.status = "suspended"
        assert hs.account == "abcdefg"
        assert hs.issn == "9876-5432"
        assert hs.status == "suspended"
        assert hs.suspended

        hs.reactivate()
        assert not hs.suspended
        hs.suspend()
        assert hs.suspended

        hs.save(blocking=True)

        hs2 = models.HarvestState.pull(hs.id)
        assert hs2.account == "abcdefg"
        assert hs2.issn == "9876-5432"
        assert hs2.status == "suspended"
        assert hs2.suspended

        # make one from source
        source = HarvestStateFactory.harvest_state()
        hs3 = models.HarvestState(source)
        hs3.save()

    def test_02_harvest_state_dao(self):
        hs = models.HarvestState()
        hs.account = "abcdefg"
        hs.issn = "9876-5432"
        hs.save()

        hs = models.HarvestState()
        hs.account = "abcdefg"
        hs.issn = "1234-5678"
        hs.save(blocking=True)

        # first check that we can find it by issn
        hs2 = models.HarvestState.find_by_issn("abcdefg", "9876-5432")

        assert hs2.issn == "9876-5432"
        assert hs2.account == "abcdefg"
        assert hs2.status == "active"

        # now check that we can find it by account
        gen = models.HarvestState.find_by_account("abcdefg")
        hss = [x for x in gen]
        assert len(hss) == 2

        # now just check the fail cases
        hs3 = models.HarvestState.find_by_issn("abcdefg", "7777-7777")
        assert hs3 is None

        gen2 = models.HarvestState.find_by_account("123456789")
        hss2 = [x for x in gen]
        assert len(hss2) == 0

    def test_03_state_changes(self):
        # the issns that we are going to pass to the state manager to prep
        issns = [
            "1111-1111", # a new issn not previously seen, which will be added
            "2222-2222", # a current active issn
            "3333-3333", # a current suspended issn
        ]

        # the issns which are currently in the harvester system

        # a current active issn, which will remain unchanged
        hs = models.HarvestState()
        hs.account = "abcdefg"
        hs.issn = "2222-2222"
        hs.save()

        # a current suspended issn, which will be reactivated
        hs = models.HarvestState()
        hs.account = "abcdefg"
        hs.issn = "3333-3333"
        hs.suspend()
        hs.save()

        # an issn that is active but missing from the update set, so will be suspended
        hs = models.HarvestState()
        hs.account = "abcdefg"
        hs.issn = "4444-4444"
        hs.save(blocking=True)

        workflow.HarvesterWorkflow.process_issn_states("abcdefg", issns)

        hs1 = models.HarvestState.find_by_issn("abcdefg", "1111-1111")
        assert hs1 is not None
        assert not hs1.suspended

        hs2 = models.HarvestState.find_by_issn("abcdefg", "2222-2222")
        assert hs2 is not None
        assert not hs2.suspended

        hs3 = models.HarvestState.find_by_issn("abcdefg", "3333-3333")
        assert hs3 is not None
        assert not hs3.suspended

        hs4 = models.HarvestState.find_by_issn("abcdefg", "4444-4444")
        assert hs4 is not None
        assert hs4.suspended

    def test_04_last_harvest(self):
        hs = models.HarvestState()
        hs.account = "abcdefg"
        hs.issn = "2222-2222"
        hs.save()

        # first check that we don't get a last harvest date for anyone
        harvesters = app.config.get("HARVESTERS", [])
        plugins = []
        for h in harvesters:
            p = plugin.load_class(h)()
            plugins.append(p)
            lh = hs.get_last_harvest(p.get_name())
            assert lh is None

        lhs = {}
        for p in plugins:
            lhs[p.get_name()] = dates.random_date()
            hs.set_harvested(p.get_name(), lhs[p.get_name()])

        hs.save(blocking=True)

        hs2 = models.HarvestState.find_by_issn("abcdefg", "2222-2222")
        for p in plugins:
            lh = hs2.get_last_harvest(p.get_name())
            assert lh == lhs[p.get_name()]


