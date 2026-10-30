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



class QualityReviewAssessment(State):
    pass
