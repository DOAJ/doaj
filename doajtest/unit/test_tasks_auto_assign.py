import time

from doajtest.helpers import DoajTestCase
from portality.background import BackgroundApi
from portality.core import app
from portality.tasks import auto_assign_editor_group_data
from portality.bll.services import application
from portality.bll import exceptions

class MockApplicationService:
    RETURN = [1,2,3]
    EXCEPT = None

    @classmethod
    def retrieve_ur_editor_group_sheets(cls, prune=True):
        if cls.EXCEPT is not None:
            raise cls.EXCEPT("error")
        return cls.RETURN

class TestTaskAutoAssign(DoajTestCase):

    def setUp(self):
        super(TestTaskAutoAssign, self).setUp()
        self.aps = application.ApplicationService
        application.ApplicationService = MockApplicationService

    def tearDown(self):
        super(TestTaskAutoAssign, self).tearDown()
        application.ApplicationService = self.aps

    def test_01_success(self):
        user = app.config.get("SYSTEM_USERNAME")
        job = auto_assign_editor_group_data.AutoAssignEditorGroupDataTask.prepare(user)
        task = auto_assign_editor_group_data.AutoAssignEditorGroupDataTask(job)
        BackgroundApi.execute(task)
        assert job.status == "complete"
        assert job.outcome_status == "success"

    def test_02_retrieve_fail(self):
        application.ApplicationService.EXCEPT = exceptions.RemoteServiceException
        user = app.config.get("SYSTEM_USERNAME")
        job = auto_assign_editor_group_data.AutoAssignEditorGroupDataTask.prepare(user)
        task = auto_assign_editor_group_data.AutoAssignEditorGroupDataTask(job)
        BackgroundApi.execute(task)
        assert job.status == "error"
        assert job.outcome_status == "fail"

    def test_02_invalid_data(self):
        application.ApplicationService.EXCEPT = ValueError
        user = app.config.get("SYSTEM_USERNAME")
        job = auto_assign_editor_group_data.AutoAssignEditorGroupDataTask.prepare(user)
        task = auto_assign_editor_group_data.AutoAssignEditorGroupDataTask(job)
        BackgroundApi.execute(task)
        assert job.status == "error"
        assert job.outcome_status == "fail"




