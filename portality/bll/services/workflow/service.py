from typing import Type, Union

from portality.bll.services.workflow.quality_review import QualityReviewAwaitingAssignment, QualityReviewAssessment
from portality.bll.services.workflow.quick_fail import QuickFailAwaitingAssignment, QuickFailCriteriaCheck
from portality.bll.services.workflow.rejected import Rejected
from portality.bll.services.workflow.triage import AwaitingTriage, TriageAssessmentInProgress, \
    TriageAssessmentMinimalReview
from portality.bll.services.workflow.core import State, WorkflowEvent, WorkflowAction
from portality.models import WorkflowControl, Account, Application


class WorkflowService:
    STATES = [
        # Triage States
        AwaitingTriage,
        TriageAssessmentInProgress,
        TriageAssessmentMinimalReview,

        # Quick Fail States
        QuickFailAwaitingAssignment,
        QuickFailCriteriaCheck,

        # Quality Review States
        QualityReviewAwaitingAssignment,
        QualityReviewAssessment,

        # Rejected State
        Rejected
    ]

    def iterate_state(self, state:Type[State]):
        query = state.query()
        for wfc in WorkflowControl.iterate_unstable(q=query.query()):
            yield state(wfc)

    def first_n_in_state(self, state:Type[State], n:int) -> list[State]:
        query = state.query()
        query.size = n
        return [state(x) for x in WorkflowControl.object_query(q=query.query())]

    def apply_action(self, wfc:Union[str, WorkflowControl], action:WorkflowAction, save=True) -> State:
        if isinstance(wfc, str):
            wfc = WorkflowControl.pull(wfc)

        state_instance = self.state_for_workflow_control(wfc)
        if state_instance is None:
            raise ValueError(f"No state found for workflow control with id '{wfc.id}'")

        new_state = self.action(state_instance, action)
        if save:
            new_state.saveall()
        return new_state

    def apply_event(self, wfc:Union[str, WorkflowControl], event:WorkflowEvent, save=True) -> State:
        if isinstance(wfc, str):
            wfc = WorkflowControl.pull(wfc)

        state_instance = self.state_for_workflow_control(wfc)
        if state_instance is None:
            raise ValueError(f"No state found for workflow control with id '{wfc.id}'")

        new_state = self.event(state_instance, event)
        if save:
            new_state.saveall()
        return new_state

    def state_for_workflow_control(self, wfc:Union[str, WorkflowControl], application:Application=None) -> Union[State, None]:
        if isinstance(wfc, str):
            wfc = WorkflowControl.pull(wfc)

        if wfc is None:
            return None

        for state in self.STATES:
            if state.matches(wfc):
                return state(wfc, application)

        return None

    def event(self, state_instance:State, event:WorkflowEvent) -> State:
        if event.__class__ not in state_instance.events:
            raise ValueError(f"Invalid event '{event}' for state '{type(state_instance).__name__}'")

        new_state = state_instance.exit(event)
        return new_state

    def action(self, state_instance:State, action:WorkflowAction) -> State:
        if action.__class__ not in state_instance.actions:
            raise ValueError(f"Invalid action '{action}' on state '{type(state_instance).__name__}'")

        new_state = state_instance.do(action)
        return new_state

    def initialise_workflow(self, actor:Union[str, Account], application:Application) -> State:
        wfc = WorkflowControl()
        wfc.application_id = application.id
        wfc.original_application = application
        wfc.application_title = application.bibjson().title
        initial_state = AwaitingTriage.enter(actor, wfc, application)
        return initial_state
