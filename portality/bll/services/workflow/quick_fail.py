from typing import Union

from portality import constants
from portality.bll.services.workflow.core import State
from portality.models import WorkflowControl, Account, Application

MODULE_QUICK_FAIL = "quick_fail"
MODULE_QUICK_FAIL_STAGE_PENDING = "pending"
LEGACY_MODULE_QUICK_FAIL = "triaged_quick_fail_legacy"
LEGACY_MODULE_QUICK_FAIL_STAGE_DEFAULT = "default"

MODULE_QUICK_FAIL_STAGES = [
    MODULE_QUICK_FAIL_STAGE_PENDING
]

LEGACY_EDITOR_GROUP = None

class QuickFailAwaitingAssignment(State):
    # These are the true QF state properties, but they are commented out for now in preference
    # of the "triaged_quick_fail_legacy" state, which is the state that records which have passed
    # through the new triage workflow and have now dropped back into the legacy workflow, but would
    # otherwise have come here for quick fail processing.

    # module = MODULE_QUICK_FAIL
    # stage = MODULE_QUICK_FAIL_STAGE_PENDING
    # reviewer = WorkflowControl.UNASSIGNED

    # Temporary states
    module = LEGACY_MODULE_QUICK_FAIL
    stage = LEGACY_MODULE_QUICK_FAIL_STAGE_DEFAULT
    reviewer = WorkflowControl.UNASSIGNED

    legacy_application_status = constants.APPLICATION_STATUS_PENDING
    legacy_editor_group = None


class QuickFailCriteriaCheck(State):
    pass
