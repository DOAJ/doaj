import time

from doajtest.helpers import DoajTestCase
from portality.background import BackgroundApi
from portality.core import app
from portality.tasks import application_autochecks
from doajtest.fixtures import ApplicationFixtureFactory
from portality import models, constants
from portality.bll.services import autochecks
from doajtest.mocks.autocheck_checkers import AutocheckMockFactory


class TestApplicationAutochecks(DoajTestCase):

    def setUp(self):
        self.old_plugins = autochecks.AUTOCHECK_PLUGINS
        autochecks.AUTOCHECK_PLUGINS = [
            (True, True, AutocheckMockFactory.mock_autochecker())
        ]
        super(TestApplicationAutochecks, self).setUp()

    def tearDown(self):
        autochecks.AUTOCHECK_PLUGINS = self.old_plugins
        super(TestApplicationAutochecks, self).tearDown()

    def test_01_application_not_found(self):
        user = app.config.get("SYSTEM_USERNAME")
        job = application_autochecks.ApplicationAutochecks.prepare(user, application="123456")
        task = application_autochecks.ApplicationAutochecks(job)
        BackgroundApi.execute(task)

        assert not job.is_failed()
        assert job.outcome_status == "success"
        assert job.status == "complete"

    def test_02_application_annotated_and_status_set(self):
        user = app.config.get("SYSTEM_USERNAME")

        source = ApplicationFixtureFactory.make_application_source()
        application = models.Application(**source)
        application.set_application_status(constants.APPLICATION_STATUS_POST_SUBMISSION_REVIEW)
        application.save(blocking=True)

        job = application_autochecks.ApplicationAutochecks.prepare(user, application=application.id, status_on_complete=constants.APPLICATION_STATUS_PENDING)
        task = application_autochecks.ApplicationAutochecks(job)
        BackgroundApi.execute(task)

        assert not job.is_failed()
        assert job.outcome_status == "success"
        assert job.status == "complete"

        time.sleep(2)
        application = models.Application.pull(application.id)
        assert application.application_status == constants.APPLICATION_STATUS_PENDING

        # check that the autocheck annotation is present
        ac = models.Autocheck.for_application(application.id)
        assert ac is not None
        assert len(ac.checks_raw) == 1


