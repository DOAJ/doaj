import time

from portality import constants
from doajtest.helpers import DoajTestCase
from portality.core import app
from portality import models
from portality.tasks.annotations import Annotations
from portality.background import BackgroundApi

from doajtest.fixtures import ApplicationFixtureFactory
from doajtest.mocks.annotation_resource_bundle_Resource import ResourceBundleResourceMockFactory

from portality.annotation.resource_bundle import Resource


class TestTaskAnnotations(DoajTestCase):

    def setUp(self):
        mock_fetch = ResourceBundleResourceMockFactory.no_contact_resource_fetch()
        self.old_fetch = Resource.fetch
        Resource.fetch = mock_fetch

        super(TestTaskAnnotations, self).setUp()

    def tearDown(self):
        Resource.fetch = self.old_fetch
        super(TestTaskAnnotations, self).tearDown()

    def test_01_workflow_new_application(self):
        source = ApplicationFixtureFactory.make_application_source()
        application = models.Application(**source)
        application.save(blocking=True)

        user = app.config.get("SYSTEM_USERNAME")
        job = Annotations.prepare(user, application=application.id)
        task = Annotations(job)
        BackgroundApi.execute(task)
        time.sleep(2)

        application = models.Application.pull(application.id)
        annotation = models.Annotation.for_application(application.id)

        assert application.application_status == constants.APPLICATION_STATUS_PENDING
        assert annotation is not None
        assert annotation.application == application.id
        assert len(annotation.annotations) == 2


