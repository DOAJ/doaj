from doajtest.fixtures import ApplicationFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import models
from portality.bll import DOAJ
from portality.bll.services.workflow import AwaitingTriage


class TestAnon(DoajTestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_01_initialise_workflow(self):
        source = ApplicationFixtureFactory.make_application_source()
        application = models.Application(**source)

        wfSvc = DOAJ.workflowService()
        state = wfSvc.initialise_workflow(application)

        assert isinstance(state, AwaitingTriage)
