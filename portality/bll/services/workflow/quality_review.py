from portality import constants
from portality.bll.services.workflow.core import State
from portality.models import WorkflowControl

MODULE_QUALITY_REVIEW = "quality_review"
MODULE_QUALITY_REVIEW_STAGE_PENDING = "pending"

MODULE_QUALITY_REVIEW_STAGES = [
    MODULE_QUALITY_REVIEW_STAGE_PENDING
]

LEGACY_EDITOR_GROUP = None


class QualityReviewAwaitingAssignment(State):
    module = MODULE_QUALITY_REVIEW
    stage = MODULE_QUALITY_REVIEW_STAGE_PENDING
    reviewer = WorkflowControl.UNASSIGNED

    legacy_application_status = constants.APPLICATION_STATUS_ON_HOLD
    legacy_editor_group = None


class QualityReviewAssessment(State):
    pass
