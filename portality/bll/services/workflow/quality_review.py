from portality import constants
from portality.bll.services.workflow.core import State
from portality.core import app
from portality.models import WorkflowControl

MODULE_INTEGRITY_ETHICS = "integrity_ethics"
MODULE_INTEGRITY_ETHICS_STAGE_PENDING = "pending"

MODULE_INTEGRITY_ETHICS_STAGES = [
    MODULE_INTEGRITY_ETHICS_STAGE_PENDING
]

LEGACY_MODULE_INTEGRITY_ETHICS = "triaged_integrity_ethics_legacy"
LEGACY_MODULE_INTEGRITY_ETHICS_STAGE_DEFAULT = "default"


class IntegrityEthicsAwaitingAssignment(State):
    # These are the true IE state properties, but they are commented out for now in preference
    # of the "triaged_quick_fail_legacy" state, which is the state that records which have passed
    # through the new triage workflow and have now dropped back into the legacy workflow, but would
    # otherwise have come here for quick fail processing.

    # module = MODULE_INTEGRITY_ETHICS
    # stage = MODULE_INTEGRITY_ETHICS_STAGE_PENDING
    # reviewer = WorkflowControl.UNASSIGNED

    # Temporary states
    module = LEGACY_MODULE_INTEGRITY_ETHICS
    stage = LEGACY_MODULE_INTEGRITY_ETHICS_STAGE_DEFAULT
    reviewer = WorkflowControl.UNASSIGNED

    legacy_application_status = constants.APPLICATION_STATUS_ON_HOLD
    legacy_editor_group = app.config.get("LEGACY_WORKFLOW_INTEGRITY_ETHICS_EDITOR_GROUP")


class QualityReviewAssessment(State):
    pass
