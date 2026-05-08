from portality import constants
from portality.bll.services.workflow.core import State
from portality.models import WorkflowControl

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

    legacy_application_status = constants.APPLICATION_STATUS_IN_PROGRESS
    legacy_editor_group = None


class QuickFailCriteriaCheck(State):
    pass
