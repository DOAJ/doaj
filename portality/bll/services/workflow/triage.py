from typing import Union

from portality import constants
from portality.bll import DOAJ
from portality.bll.exceptions import AuthoriseException

from portality.bll.services.workflow.core import WorkflowEvent, State, Claim, Assign, Unclaim, Reassign, Unassign, \
    Fail, ApplicationEdit, WorkflowAction
from portality.bll.services.workflow.rejected import Rejected
from portality.models import Account, WorkflowControl

########################################
# Triage module state definition values

MODULE_TRIAGE = "triage"
MODULE_TRIAGE_STAGE_IN_PROGRESS = "in_progress"
MODULE_TRIAGE_STAGE_MINIMAL_REVIEW = "minimal_review"
MODULE_TRIAGE_STAGES = [
    MODULE_TRIAGE_STAGE_IN_PROGRESS,
    MODULE_TRIAGE_STAGE_MINIMAL_REVIEW
]

LEGACY_EDITOR_GROUP = None

######################################
## Workflow events specific to Triage

class MinimalReview(WorkflowEvent): pass

class RescindMinimalReview(WorkflowEvent): pass

class Triaged(WorkflowEvent):
    def __init__(self, actor:Union[str, Account], label:str):
        super().__init__(actor)
        self._label = label

    @property
    def label(self):
        return self._label

######################################
## Triage Workflow States

class AwaitingTriage(State):
    module = MODULE_TRIAGE
    stage = WorkflowControl.ANY
    reviewer = WorkflowControl.UNASSIGNED

    legacy_application_status = constants.APPLICATION_STATUS_NEW_WORKFLOW
    legacy_editor_group = LEGACY_EDITOR_GROUP

    events = [Claim, Assign]

    def apply_stage(self):
        wf_control = self.workflow_control
        if wf_control.stage not in MODULE_TRIAGE_STAGES:
            if wf_control.triage.review_complete:
                wf_control.stage = MODULE_TRIAGE_STAGE_MINIMAL_REVIEW
            else:
                wf_control.stage = MODULE_TRIAGE_STAGE_IN_PROGRESS

    def exit(self, event:WorkflowEvent) -> State:
        return self.dispatch_event(event, {
            Claim: self.event_claim,
            Assign: self.event_assign
        })

    def event_claim(self, event:Claim) -> State:
        return self._assign_and_transition(event.actor, event.actor)

    def event_assign(self, event:Assign) -> State:
        if not event.actor.has_role(constants.ROLE_ADMIN):
            raise AuthoriseException(reason=AuthoriseException.WRONG_ROLE)
        return self._assign_and_transition(event.actor, event.reviewer)

    def _assign_and_transition(self, actor, reviewer) -> Union["TriageAssessmentInProgress", "TriageAssessmentMinimalReview"]:
        if not reviewer.has_attribute(constants.USER_ATTR__WORKFLOW, constants.EWF__TRIAGE):
            raise AuthoriseException(reason=AuthoriseException.WRONG_ATTRIBUTE)

        wfc = self.workflow_control
        wfc.reviewer_id = reviewer.id

        # legacy bindings
        # TODO: if a reviewer is assigned, but no editor group, do we get any inconsistent behaviour
        if self.application is None:
            raise ValueError("WorkflowControl is not bound to an application, cannot apply legacy bindings")
        if self.legacy_editor_group:
            self.application.set_editor_group(self.legacy_editor_group)
        else:
            self.application.remove_editor_group()
        self.application.set_editor(reviewer.id)

        if wfc.triage.review_complete:
            return self.transition(TriageAssessmentMinimalReview, actor)
        else:
            return self.transition(TriageAssessmentInProgress, actor)


class TriageWorkingState(State):
    def do(self, action:WorkflowAction) -> State:
        if isinstance(action, ApplicationEdit):
            return self.do_edit(action)
        else:
            raise ValueError(f"Unknown action '{action}' for state '{type(self).__name__}'")

    def do_edit(self, action:ApplicationEdit) -> State:
        raise NotImplementedError("do_edit must be implemented by subclasses of TriageWorkingState")

    def event_unclaim(self, event:Unclaim) -> AwaitingTriage:
        wfc = self.workflow_control
        if wfc.reviewer_id != event.actor_id:
            raise AuthoriseException(reason=AuthoriseException.NOT_AUTHORISED)

        del wfc.reviewer_id

        # legacy bindings
        if self.application is None:
            raise ValueError("WorkflowControl is not bound to an application, cannot apply legacy bindings")

        self.application.remove_editor()
        if self.legacy_editor_group:
            self.application.set_editor_group(self.legacy_editor_group)
        else:
            self.application.remove_editor_group()

        return self.transition(AwaitingTriage, event.actor)

    def event_unassign(self, event:Unassign) -> AwaitingTriage:
        wfc = self.workflow_control
        if not event.actor.has_role(constants.ROLE_ADMIN):
            raise AuthoriseException(reason=AuthoriseException.WRONG_ROLE)

        del wfc.reviewer_id

        # legacy bindings
        if self.application is None:
            raise ValueError("WorkflowControl is not bound to an application, cannot apply legacy bindings")

        self.application.remove_editor()
        if self.legacy_editor_group:
            self.application.set_editor_group(self.legacy_editor_group)
        else:
            self.application.remove_editor_group()

        return self.transition(AwaitingTriage, event.actor)

    def event_reassign(self, event:Reassign) -> "TriageWorkingState":
        wfc = self.workflow_control
        if not event.actor.has_role(constants.ROLE_ADMIN):
            raise AuthoriseException(reason=AuthoriseException.WRONG_ROLE)

        if not event.reviewer.has_attribute(constants.USER_ATTR__WORKFLOW, constants.EWF__TRIAGE):
            raise AuthoriseException(reason=AuthoriseException.WRONG_ATTRIBUTE)

        wfc.reviewer_id = event.reviewer_id

        # legacy bindings
        if self.application is None:
            raise ValueError("WorkflowControl is not bound to an application, cannot apply legacy bindings")

        self.application.set_editor(event.reviewer_id)
        if self.legacy_editor_group:
            self.application.set_editor_group(self.legacy_editor_group)
        else:
            self.application.remove_editor_group()

        return self.enter(event.actor, self._wf_control, self._application, self)

    def event_fail(self, event: Fail) -> "Rejected":
        wfc = self.workflow_control
        reviewer_permission = wfc.reviewer_id == event.actor_id and wfc.reviewer.has_attribute(
            constants.USER_ATTR__WORKFLOW, constants.EWF__TRIAGE)
        if not reviewer_permission:
            raise AuthoriseException(reason=AuthoriseException.NOT_AUTHORISED)

        # remove the editor
        del wfc.reviewer_id

        # legacy bindings
        if self.application is None:
            raise ValueError("WorkflowControl is not bound to an application, cannot apply legacy bindings")
        self.application.remove_editor()
        self.application.remove_editor_group()

        appSvc = DOAJ.applicationService()
        appSvc.reject_application(self.application, event.actor, note=event.note)

        # TODO: not clear what to do with application embargoes, perhaps these are a new type?

        from portality.bll.services.workflow.rejected import Rejected
        return self.transition(Rejected, event.actor)


class TriageAssessmentInProgress(TriageWorkingState):
    module = MODULE_TRIAGE
    stage = MODULE_TRIAGE_STAGE_IN_PROGRESS
    reviewer = WorkflowControl.ASSIGNED

    legacy_application_status = constants.APPLICATION_STATUS_IN_PROGRESS
    legacy_editor_group = LEGACY_EDITOR_GROUP

    events = [Unclaim, Reassign, Unassign, Fail, MinimalReview]
    actions = [ApplicationEdit]

    def apply(self):
        super(TriageAssessmentInProgress, self).apply()
        self.workflow_control.triage.review_complete = False

    def do_edit(self, action:ApplicationEdit) -> Union["TriageAssessmentInProgress", "TriageAssessmentMinimalReview"]:
        wfc = self.workflow_control
        reviewer_permission = wfc.reviewer_id == action.actor_id and wfc.reviewer.has_attribute(constants.USER_ATTR__WORKFLOW, constants.EWF__TRIAGE)
        if not (reviewer_permission or action.actor.has_role(constants.ROLE_ADMIN)):
            raise AuthoriseException(reason=AuthoriseException.NOT_AUTHORISED)

        # FIXME: where does has_minimal_review get calculated?
        if self.workflow_control.triage.review_complete:
            return self.event_minimal_review(MinimalReview(action.actor_id))
        else:
            return self

    def exit(self, event:WorkflowEvent) -> State:
        return self.dispatch_event(event, {
            Unclaim: self.event_unclaim,
            Unassign: self.event_unassign,
            Reassign: self.event_reassign,
            Fail: self.event_fail,
            MinimalReview: self.event_minimal_review
        })

    def event_minimal_review(self, event: MinimalReview) -> "TriageAssessmentMinimalReview":
        wfc = self.workflow_control
        reviewer_permission = wfc.reviewer_id == event.actor_id and wfc.reviewer.has_attribute(
            constants.USER_ATTR__WORKFLOW, constants.EWF__TRIAGE)

        if not (reviewer_permission or event.actor.has_role(constants.ROLE_ADMIN)):
            raise AuthoriseException(reason=AuthoriseException.NOT_AUTHORISED)

        wfc.triage.review_complete = True
        return self.transition(TriageAssessmentMinimalReview, event.actor)


class TriageAssessmentMinimalReview(TriageWorkingState):
    module = MODULE_TRIAGE
    stage = MODULE_TRIAGE_STAGE_MINIMAL_REVIEW
    reviewer = WorkflowControl.ASSIGNED

    legacy_application_status = constants.APPLICATION_STATUS_IN_PROGRESS
    legacy_editor_group = LEGACY_EDITOR_GROUP

    events = [Triaged, Unclaim, Reassign, Unassign, Fail, RescindMinimalReview]
    actions = [ApplicationEdit]

    def apply(self):
        super(TriageAssessmentMinimalReview, self).apply()
        self.workflow_control.triage.review_complete = True

    def do_edit(self, action: ApplicationEdit) -> Union["TriageAssessmentInProgress", "TriageAssessmentMinimalReview"]:
        wfc = self.workflow_control
        reviewer_permission = wfc.reviewer_id == action.actor_id and wfc.reviewer.has_attribute(
            constants.USER_ATTR__WORKFLOW, constants.EWF__TRIAGE)
        if not (reviewer_permission or action.actor.has_role(constants.ROLE_ADMIN)):
            raise AuthoriseException(reason=AuthoriseException.NOT_AUTHORISED)

        # FIXME: where does has_minimal_review get calculated?
        if self.workflow_control.triage.review_complete:
            return self
        else:
            return self.event_rescind_minimal_review(RescindMinimalReview(action.actor_id))

    def exit(self, event: WorkflowEvent) -> State:
        return self.dispatch_event(event, {
            Unclaim: self.event_unclaim,
            Unassign: self.event_unassign,
            Reassign: self.event_reassign,
            RescindMinimalReview: self.event_rescind_minimal_review,
            Fail: self.event_fail,
            Triaged: self.event_triaged
        })

    def event_rescind_minimal_review(self, event: RescindMinimalReview) -> TriageAssessmentInProgress:
        wfc = self.workflow_control
        reviewer_permission = wfc.reviewer_id == event.actor_id and wfc.reviewer.has_attribute(
            constants.USER_ATTR__WORKFLOW, constants.EWF__TRIAGE)
        if not (reviewer_permission or event.actor.has_role(constants.ROLE_ADMIN)):
            raise AuthoriseException(reason=AuthoriseException.NOT_AUTHORISED)

        wfc.triage.review_complete = False
        return self.transition(TriageAssessmentInProgress, event.actor)

    def event_triaged(self, event: Triaged) -> Union["QuickFailAwaitingAssignment", "QualityReviewAwaitingAssignment"]:
        wfc = self.workflow_control
        reviewer_permission = wfc.reviewer_id == event.actor_id and wfc.reviewer.has_attribute(
            constants.USER_ATTR__WORKFLOW, constants.EWF__TRIAGE)
        if not reviewer_permission:
            raise AuthoriseException(reason=AuthoriseException.NOT_AUTHORISED)

        # add the triage label(s)
        wfc.add_label(event.label)

        # unassign the reviewer
        del wfc.reviewer_id

        # legacy bindings
        if self.application is None:
            raise ValueError("WorkflowControl is not bound to an application, cannot apply legacy bindings")
        self.application.remove_editor()
        self.application.remove_editor_group()

        if event.label == constants.EWF__QUICK_FAIL:
            from portality.bll.services.workflow.quick_fail import QuickFailAwaitingAssignment
            return self.transition(QuickFailAwaitingAssignment, event.actor)
        elif event.label == constants.EWF__QUALITY_REVIEW:
            from portality.bll.services.workflow.quality_review import QualityReviewAwaitingAssignment
            return self.transition(QualityReviewAwaitingAssignment, event.actor)
        else:
            raise ValueError(f"Unknown triage label '{event.label}'")

