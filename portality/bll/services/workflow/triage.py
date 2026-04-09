from typing import Union

from portality import constants
from portality.bll import DOAJ
from portality.bll.exceptions import AuthoriseException

from portality.bll.services.workflow.core import WorkflowEvent, State, Claim, Assign, Unclaim, Reassign, Unassign, \
    Fail, ApplicationEdit, WorkflowAction
from portality.models import Account, EditorGroup, WorkflowControl

########################################
# Triage module state definition values

MODULE_TRIAGE = "triage"
MODULE_TRIAGE_STAGE_IN_PROGRESS = "in_progress"
MODULE_TRIAGE_STAGE_MINIMAL_REVIEW = "minimal_review"
MODULE_TRIAGE_STAGES = [
    MODULE_TRIAGE_STAGE_IN_PROGRESS,
    MODULE_TRIAGE_STAGE_MINIMAL_REVIEW
]
MODULE_TRIAGE_EG = "Triage"

######################################
## Workflow events specific to Triage

class MinimalReview(WorkflowEvent): pass

class RescindMinimalReview(WorkflowEvent): pass

class Triaged(WorkflowEvent):
    def __init__(self, actor:Union[str, Account],
                 target_editor_group:Union[str, EditorGroup]=None,
                 target_maned:Union[str, Account]=None):
        super().__init__(actor)
        self._editor_group = target_editor_group
        self._maned = target_maned

    @property
    def editor_group(self):
        return self._editor_group

    @property
    def maned(self):
        return self._maned

######################################
## Triage Workflow States

class AwaitingTriage(State):
    module = MODULE_TRIAGE
    stage = WorkflowControl.ANY
    editor_group = MODULE_TRIAGE_EG
    reviewer = WorkflowControl.UNASSIGNED

    events = [Claim, Assign]

    def apply(self):
        # Ensure the workflow control object is in the right state
        wf_control = self.workflow_control
        if wf_control.module != self.module:
            wf_control.module = self.module

        if wf_control.stage not in MODULE_TRIAGE_STAGES:
            if wf_control.triage.has_minimal_review:
                wf_control.stage = MODULE_TRIAGE_STAGE_MINIMAL_REVIEW
            else:
                wf_control.stage = MODULE_TRIAGE_STAGE_IN_PROGRESS

        if wf_control.editor_group != self.editor_group:
            wf_control.editor_group = self.editor_group
            wf_control.reviewer = None

        # back-compatibility for the original workflow
        application = self.application

        if application.application_status != constants.APPLICATION_STATUS_PENDING:
            application.set_application_status(constants.APPLICATION_STATUS_PENDING)

        if application.editor_group != self.editor_group:
            application.set_editor_group(self.editor_group)
            application.remove_editor()

    def exit(self, event:WorkflowEvent):
        if isinstance(event, Claim):
            return self.event_claim(event)
        elif isinstance(event, Assign):
            return self.event_assign(event)
        else:
            raise ValueError(f"Unknown event '{event}' for state '{type(self).__name__}'")

    def event_claim(self, event:Claim):
        wfc = self.workflow_control
        # FIXME: needs to be resolved with feature vs role capability
        if not event.actor.has_role(constants.ROLE_TRIAGE):
            raise AuthoriseException(reason=AuthoriseException.WRONG_ROLE)

        wfc.reviewer = event.actor_id
        if wfc.triage.has_minimal_review:
            return TriageAssessmentMinimalReview.enter(event.actor, self._wf_control, self._application, self)
        else:
            return TriageAssessmentInProgress.enter(event.actor, self._wf_control, self._application, self)

    def event_assign(self, event:Assign):
        wfc = self.workflow_control
        # FIXME: needs to be resolved with feature vs role capability
        if not (event.actor.has_role(constants.ROLE_TRIAGE) or event.actor.has_role(constants.ROLE_ADMIN)):
            raise AuthoriseException(reason=AuthoriseException.WRONG_ROLE)
        if not event.reviewer.has_role(constants.ROLE_TRIAGE):
            raise AuthoriseException(reason=AuthoriseException.WRONG_ROLE)

        wfc.reviewer = event.reviewer_id
        if wfc.triage.has_minimal_review:
            return TriageAssessmentMinimalReview.enter(event.actor, self._wf_control, self._application, self)
        else:
            return TriageAssessmentInProgress.enter(event.actor, self._wf_control, self._application, self)


class TriageAssessmentInProgress(State):
    module = MODULE_TRIAGE
    stage = MODULE_TRIAGE_STAGE_IN_PROGRESS
    editor_group = MODULE_TRIAGE_EG
    reviewer = WorkflowControl.ASSIGNED

    events = [Unclaim, Reassign, Unassign, Fail, MinimalReview]
    actions = [ApplicationEdit]

    def apply(self):
        # Ensure the workflow control object is in the right state
        wf_control = self.workflow_control
        if wf_control.module != self.module:
            wf_control.module = self.module

        if wf_control.stage != self.stage:
            wf_control.stage = self.stage

        if wf_control.editor_group != self.editor_group:
            wf_control.editor_group = self.editor_group

        if wf_control.reviewer is None:
            raise ValueError("Reviewer must be set for TriageAssessmentInProgress state")

        # back-compatibility for the original workflow
        application = self.application

        if application.application_status != constants.APPLICATION_STATUS_IN_PROGRESS:
            application.set_application_status(constants.APPLICATION_STATUS_IN_PROGRESS)

        if application.editor_group != self.editor_group:
            application.set_editor_group(self.editor_group)

        if application.editor != wf_control.reviewer:
            application.set_editor(wf_control.reviewer)

    def exit(self, event:WorkflowEvent):
        if isinstance(event, Unclaim):
            return self.event_unclaim(event)
        elif isinstance(event, Reassign):
            return self.event_reassign(event)
        elif isinstance(event, Unassign):
            return self.event_unassign(event)
        elif isinstance(event, Fail):
            return self.event_fail(event)
        elif isinstance(event, MinimalReview):
            return self.event_minimal_review(event)
        else:
            raise ValueError(f"Unknown event '{event}' for state '{type(self).__name__}'")

    def do(self, action:WorkflowAction):
        if isinstance(action, ApplicationEdit):
            self.do_edit(action)
        else:
            raise ValueError(f"Unknown action '{action}' for state '{type(self).__name__}'")

    def event_unclaim(self, event:Unclaim):
        wfc = self.workflow_control
        if wfc.reviewer != event.actor_id:
            raise AuthoriseException(reason=AuthoriseException.NOT_AUTHORISED)

        del wfc.reviewer
        return AwaitingTriage.enter(event.actor, self._wf_control, self._application, self)

    def event_reassign(self, event:Reassign):
        wfc = self.workflow_control
        if not event.actor.has_role(constants.ROLE_ADMIN):
            raise AuthoriseException(reason=AuthoriseException.WRONG_ROLE)

        wfc.reviewer = event.reviewer_id
        return self.enter(event.actor, self._wf_control, self._application, self)

    def event_unassign(self, event:Unassign):
        wfc = self.workflow_control
        if not event.actor.has_role(constants.ROLE_ADMIN):
            raise AuthoriseException(reason=AuthoriseException.WRONG_ROLE)

        del wfc.reviewer
        return AwaitingTriage.enter(event.actor, self._wf_control, self._application, self)

    def event_fail(self, event:Fail):
        wfc = self.workflow_control
        if wfc.reviewer != event.actor_id:
            raise AuthoriseException(reason=AuthoriseException.NOT_AUTHORISED)

        appSvc = DOAJ.applicationService()
        appSvc.reject_application(self.application, event.actor, note=event.note)

        del wfc.editor_group
        del wfc.reviewer

        # TODO: not clear what to do with application embargoes, perhaps these are a new type?
        from portality.bll.services.workflow.rejected import Rejected
        return Rejected.enter(event.actor, self._wf_control, self._application, self)

    def event_minimal_review(self, event: MinimalReview):
        wfc = self.workflow_control
        if wfc.reviewer != event.actor_id:
            raise AuthoriseException(reason=AuthoriseException.NOT_AUTHORISED)

        wfc.triage.has_minimal_review = True
        return TriageAssessmentMinimalReview.enter(event.actor, self._wf_control, self._application, self)

    def do_edit(self, action:ApplicationEdit):
        wfc = self.workflow_control
        if wfc.reviewer != action.actor_id:
            raise AuthoriseException(reason=AuthoriseException.NOT_AUTHORISED)

        # FIXME: where does has_minimal_review get calculated?
        if self.workflow_control.triage.has_minimal_review:
            return self.event_minimal_review(MinimalReview(action.actor_id))
        else:
            return self


class TriageAssessmentMinimalReview(State):
    module = MODULE_TRIAGE
    stage = MODULE_TRIAGE_STAGE_MINIMAL_REVIEW
    editor_group = MODULE_TRIAGE_EG
    reviewer = WorkflowControl.ASSIGNED

    events = [Triaged, Unclaim, Reassign, Unassign, Fail, RescindMinimalReview]
    actions = [ApplicationEdit]

    def apply(self):
        # Ensure the workflow control object is in the right state
        wf_control = self.workflow_control
        if wf_control.module != self.module:
            wf_control.module = self.module

        if wf_control.stage != self.stage:
            wf_control.stage = self.stage

        if wf_control.editor_group != self.editor_group:
            wf_control.editor_group = self.editor_group

        if wf_control.reviewer is None:
            raise ValueError("Reviewer must be set for TriageAssessmentMinimalReview state")

        # back-compatibility for the original workflow
        application = self.application

        if application.application_status != constants.APPLICATION_STATUS_IN_PROGRESS:
            application.set_application_status(constants.APPLICATION_STATUS_IN_PROGRESS)

        if application.editor_group != self.editor_group:
            application.set_editor_group(self.editor_group)

        if application.editor != wf_control.reviewer:
            application.set_editor(wf_control.reviewer)

    def exit(self, event: WorkflowEvent):
        if isinstance(event, Triaged):
            return self.event_triaged(event)
        elif isinstance(event, Unclaim):
            return self.event_unclaim(event)
        elif isinstance(event, Reassign):
            return self.event_reassign(event)
        elif isinstance(event, Unassign):
            return self.event_unassign(event)
        elif isinstance(event, Fail):
            return self.event_fail(event)
        elif isinstance(event, RescindMinimalReview):
            return self.event_rescind_minimal_review(event)
        else:
            raise ValueError(f"Unknown event '{event}' for state '{type(self).__name__}'")

    def do(self, action: WorkflowAction):
        if isinstance(action, ApplicationEdit):
            self.do_edit(action)
        else:
            raise ValueError(f"Unknown action '{action}' for state '{type(self).__name__}'")

    def event_triaged(self, event: Triaged):
        wfc = self.workflow_control
        if wfc.reviewer != event.actor_id:
            raise AuthoriseException(reason=AuthoriseException.NOT_AUTHORISED)

        if event.maned is not None:
            groups = EditorGroup.groups_by_editor(event.maned)
            vessel = None
            for g in groups:
                if len(g.associates) > 0:
                    continue
                if g.name.lower() != event.maned.lower():
                    continue
                vessel = g
                break

            if vessel is None:
                raise ValueError(f"Maned '{event.maned}' is not the editor of a managing editor's special vessel group")

            wfc.editor_group = vessel.name
            wfc.reviewer = event.maned

            from portality.bll.services.workflow.quick_fail import QuickFailCriteriaCheck
            return QuickFailCriteriaCheck.enter(event.actor, self._wf_control, self._application, self)

        elif event.editor_group is not None:
            eg = EditorGroup.pull(event.editor_group)
            if eg is None:
                raise ValueError(f"EditorGroup '{event.editor_group}' does not exist")

            wfc.editor_group = eg.name
            del wfc.reviewer

            from portality.bll.services.workflow.quick_fail import QuickFailAwaitingAssignment
            return QuickFailAwaitingAssignment.enter(event.actor, self._wf_control, self._application, self)

        raise ValueError("Triaged event must have either a target maned or a target editor group")

    def event_unclaim(self, event: Unclaim):
        wfc = self.workflow_control
        if wfc.reviewer != event.actor_id:
            raise AuthoriseException(reason=AuthoriseException.NOT_AUTHORISED)

        del wfc.reviewer
        return AwaitingTriage.enter(event.actor, self._wf_control, self._application, self)

    def event_reassign(self, event: Reassign):
        wfc = self.workflow_control
        if not event.actor.has_role(constants.ROLE_ADMIN):
            raise AuthoriseException(reason=AuthoriseException.WRONG_ROLE)

        wfc.reviewer = event.reviewer_id
        return self.enter(event.actor, self._wf_control, self._application, self)

    def event_unassign(self, event:Unassign):
        wfc = self.workflow_control
        if not event.actor.has_role(constants.ROLE_ADMIN):
            raise AuthoriseException(reason=AuthoriseException.WRONG_ROLE)

        del wfc.reviewer
        return AwaitingTriage.enter(event.actor, self._wf_control, self._application, self)

    def event_fail(self, event: Fail):
        wfc = self.workflow_control
        if wfc.reviewer != event.actor_id:
            raise AuthoriseException(reason=AuthoriseException.NOT_AUTHORISED)

        appSvc = DOAJ.applicationService()
        appSvc.reject_application(self.application, event.actor, note=event.note)

        del wfc.editor_group
        del wfc.reviewer

        # TODO: not clear what to do with application embargoes, perhaps these are a new type?

        from portality.bll.services.workflow.rejected import Rejected
        return Rejected.enter(event.actor, self._wf_control, self._application, self)

    def event_rescind_minimal_review(self, event: RescindMinimalReview):
        wfc = self.workflow_control
        if wfc.reviewer != event.actor_id:
            raise AuthoriseException(reason=AuthoriseException.NOT_AUTHORISED)

        wfc.triage.has_minimal_review = False
        return TriageAssessmentInProgress.enter(event.actor, self._wf_control, self._application, self)

    def do_edit(self, action: ApplicationEdit):
        wfc = self.workflow_control
        if wfc.reviewer != action.actor_id:
            raise AuthoriseException(reason=AuthoriseException.NOT_AUTHORISED)

        # FIXME: where does has_minimal_review get calculated?
        if self.workflow_control.triage.has_minimal_review:
            return self
        else:
            return self.event_rescind_minimal_review(RescindMinimalReview(action.actor_id))
