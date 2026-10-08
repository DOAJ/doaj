from typing import Union

from portality import constants
from portality.bll.services.workflow.core import State
from portality.models import WorkflowControl, Account, Application

MODULE_QUICK_FAIL = "quick_fail"
MODULE_QUICK_FAIL_STAGE_PENDING = "pending"

MODULE_QUICK_FAIL_STAGES = [
    MODULE_QUICK_FAIL_STAGE_PENDING
]

LEGACY_EDITOR_GROUP = None

class QuickFailAwaitingAssignment(State):
    module = MODULE_QUICK_FAIL
    stage = MODULE_QUICK_FAIL_STAGE_PENDING
    reviewer = WorkflowControl.UNASSIGNED

    legacy_application_status = constants.APPLICATION_STATUS_PENDING
    legacy_editor_group = LEGACY_EDITOR_GROUP

    def apply_legacy_application_reviewer(self):
        # back-compatibility for the original workflow
        # application = self.application
        # application.set_editor_group(self.legacy_editor_group)
        # if self.workflow_control.reviewer_id is not None:
        #     if application.editor != self.workflow_control.reviewer_id:
        #         application.set_editor(self.workflow_control.reviewer_id)
        # else:
        #     application.remove_editor()

        # FIXME: this bit will need to assign the editor group according to
        # the labelling on the record
        pass


class QuickFailCriteriaCheck(State):
    pass
