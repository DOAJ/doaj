from typing import Type, Union

from portality import models, constants
from portality.bll import DOAJ
from portality.bll.exceptions import AuthoriseException
from portality.models import Account, EditorGroup

# Generic state definition values
ANY = "*"
UNASSIGNED = "-"
ASSIGNED = "+"

# Triage module state definition values
MODULE_TRIAGE = "triage"
MODULE_TRIAGE_STAGE_IN_PROGRESS = "in_progress"
MODULE_TRIAGE_STAGE_MINIMAL_REVIEW = "minimal_review"
MODULE_TRIAGE_STAGES = [
    MODULE_TRIAGE_STAGE_IN_PROGRESS,
    MODULE_TRIAGE_STAGE_MINIMAL_REVIEW
]
MODULE_TRIAGE_EG = "Triage"

class WorkflowControlStateQuery:
    def __init__(self,
                 module:str=None,
                 stage:str=None,
                 editor_group:str=None,
                 reviewer:str=None,
                 size:int=100):
        self._module = module
        self._stage = stage
        self._editor_group = editor_group
        self._reviewer = reviewer
        self._size = size

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, size:int):
        self._size = size

    def query(self):
        must = []
        must_not = []

        if self._module is not None:
            if self._module != ANY:
                if self._module == UNASSIGNED:
                    must_not.append({"exists": {"field": "state.module"}})
                elif self._module == ASSIGNED:
                    must.append({"exists": {"field": "state.module"}})
                else:
                    must.append({"term": {"state.module.exact": self._module}})

        if self._stage is not None:
            if self._stage != ANY:
                if self._stage == UNASSIGNED:
                    must_not.append({"exists": {"field": "state.stage"}})
                elif self._stage == ASSIGNED:
                    must.append({"exists": {"field": "state.stage"}})
                else:
                    must.append({"term": {"state.stage.exact": self._stage}})

        if self._editor_group is not None:
            if self._editor_group != ANY:
                if self._editor_group == UNASSIGNED:
                    must_not.append({"exists": {"field": "state.editor_group"}})
                elif self._editor_group == ASSIGNED:
                    must.append({"exists": {"field": "state.editor_group"}})
                else:
                    must.append({"term": {"state.editor_group.exact": self._editor_group}})

        if self._reviewer is not None:
            if self._reviewer != ANY:
                if self._reviewer == UNASSIGNED:
                    must_not.append({"exists": {"field": "state.reviewer"}})
                elif self._reviewer == ASSIGNED:
                    must.append({"exists": {"field": "state.reviewer"}})
                else:
                    must.append({"term": {"state.reviewer.exact": self._reviewer}})

        bool = {}
        if len(must) > 0:
            bool["must"] = must
        if len(must_not) > 0:
            bool["must_not"] = must_not
        q = {"query": {"bool": bool}}

        q["sort"] = {"created_date": {"order": "asc"}}

        return q

class WorkflowEvent:
    def __init__(self, actor:Union[str, Account]):
        self._actor = actor

    @property
    def actor(self) -> Account:
        if isinstance(self._actor, str):
            self._actor = Account.pull(self._actor)
        return self._actor

    @property
    def actor_id(self) -> str:
        if isinstance(self._actor, str):
            return self._actor
        return self._actor.id

class WorkflowAction:
    def __init__(self, actor: Union[str, Account]):
        self._actor = actor

    @property
    def actor(self) -> Account:
        if isinstance(self._actor, str):
            self._actor = Account.pull(self._actor)
        return self._actor

    @property
    def actor_id(self) -> str:
        if isinstance(self._actor, str):
            return self._actor
        return self._actor.id

class State:
    module = None
    stage = None
    editor_group = None
    reviewer = None

    events = []
    actions = []

    def __init__(self, wf_control:models.WorkflowControl, application:models.Application=None):
        self._wf_control = wf_control
        self._application = application

    @classmethod
    def query(cls):
        return WorkflowControlStateQuery(cls.module, cls.stage, cls.editor_group, cls.reviewer)

    @classmethod
    def enter(cls, wf_control:models.WorkflowControl, application:models.Application=None):
        instance = cls(wf_control, application)
        instance.apply()
        return instance

    @classmethod
    def matches(cls, wf_control:models.WorkflowControl):
        # Check the module.
        # If the wfc has no module, and the state definition requires a specific module, then it doesn't match.
        # If the wfc has a module, and the state definition requires a specifc module, and it isn't this one, then it doesn't match
        if wf_control.module is None:
            if not (cls.module == ANY):
                return False
        else:
            if not (cls.module == ANY or cls.module == wf_control.module):
                return False

        # if we get to here, module matches

        # check the stage
        # If the wfc has no stage, and the state definition requires a specific stage, then it doesn't match.
        # If the wfc has a stage, and the state definition requires a specifc stage, and it isn't this one, then it doesn't match
        if wf_control.stage is None:
            if not (cls.stage == ANY):
                return False
        else:
            if not (cls.stage == ANY or cls.stage == wf_control.stage):
                return False

        # by here, module and stage match

        # check the editor group
        # if the wfc has no eg, then if the allowed editor group is not ANY or UNASSIGNED), no match
        # if the wfc has an eg, then if the allowed editor group is not ANY or ASSIGNED or the same as the wfc's eg, no match
        if wf_control.editor_group is None:
            if not (cls.editor_group == ANY or cls.editor_group == UNASSIGNED):
                return False
        else:
            if not (cls.editor_group == ANY or cls.editor_group == ASSIGNED or cls.editor_group == wf_control.editor_group):
                return False

        # by here, module, stage and editor group match

        if wf_control.reviewer is None:
            if not (cls.reviewer == ANY or cls.reviewer == UNASSIGNED):
                return False
        else:
            if not (cls.reviewer == ANY or cls.reviewer == ASSIGNED or cls.reviewer == wf_control.editor_group):
                return False

        return True

    @property
    def workflow_control(self):
        return self._wf_control

    @property
    def application(self):
        if self._application is None:
            app_id = self.workflow_control.application_id
            self._application = models.Application.pull(app_id)
        return self._application

    def apply(self):
        pass

    def exit(self, event:WorkflowEvent):
        return self

    def do(self, action:WorkflowAction):
        return self

    def saveall(self, *args, **kwargs):
        self.workflow_control.save(*args, **kwargs)
        if self._application:
            self._application.save(*args, **kwargs)


class ReviewerAssignment(WorkflowEvent):
    def __init__(self, actor:Union[str, Account], reviewer:Union[str, Account]):
        super().__init__(actor)
        self._reviewer = reviewer

    @property
    def reviewer(self) -> Account:
        if isinstance(self._reviewer, str):
            self._reviewer = Account.pull(self._reviewer)
        return self._reviewer

    @property
    def reviewer_id(self) -> str:
        if isinstance(self._reviewer, str):
            return self._reviewer
        return self._reviewer.id

class Claim(WorkflowEvent): pass

class Unclaim(WorkflowEvent): pass

class Assign(ReviewerAssignment): pass

class Reassign(ReviewerAssignment): pass

class Fail(WorkflowEvent): pass

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


class ApplicationEdit(WorkflowAction): pass

class AwaitingTriage(State):
    module = MODULE_TRIAGE
    stage = ANY
    editor_group = MODULE_TRIAGE_EG
    reviewer = UNASSIGNED

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
            return TriageAssessmentMinimalReview.enter(self._wf_control, self._application)
        else:
            return TriageAssessmentInProgress.enter(self._wf_control, self._application)

    def event_assign(self, event:Assign):
        wfc = self.workflow_control
        # FIXME: needs to be resolved with feature vs role capability
        if not (event.actor.has_role(constants.ROLE_TRIAGE) or event.actor.has_role(constants.ROLE_ADMIN)):
            raise AuthoriseException(reason=AuthoriseException.WRONG_ROLE)
        if not event.reviewer.has_role(constants.ROLE_TRIAGE):
            raise AuthoriseException(reason=AuthoriseException.WRONG_ROLE)

        wfc.reviewer = event.reviewer_id
        if wfc.triage.has_minimal_review:
            return TriageAssessmentMinimalReview.enter(self._wf_control, self._application)
        else:
            return TriageAssessmentInProgress.enter(self._wf_control, self._application)

class TriageAssessmentInProgress(State):
    module = MODULE_TRIAGE
    stage = MODULE_TRIAGE_STAGE_IN_PROGRESS
    editor_group = MODULE_TRIAGE_EG
    reviewer = ASSIGNED

    events = [Unclaim, Reassign, Fail, MinimalReview]
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
        return AwaitingTriage.enter(self._wf_control, self._application)

    def event_reassign(self, event:Reassign):
        wfc = self.workflow_control
        if not event.actor.has_role(constants.ROLE_ADMIN):
            raise AuthoriseException(reason=AuthoriseException.WRONG_ROLE)

        wfc.reviewer = event.reviewer_id
        return self.enter(self._wf_control, self._application)

    def event_fail(self, event:Fail):
        # TODO: we don't know where this goes yet
        raise NotImplementedError()

    def event_minimal_review(self, event:MinimalReview):
        wfc = self.workflow_control
        if wfc.reviewer != event.actor_id:
            raise AuthoriseException(reason=AuthoriseException.NOT_AUTHORISED)

        wfc.triage.has_minimal_review = True
        return TriageAssessmentMinimalReview.enter(self._wf_control, self._application)

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
    reviewer = ASSIGNED

    events = [Triaged, Unclaim, Reassign, Fail, RescindMinimalReview]
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

    def event_triaged(self, event:Triaged):
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

            return QuickFailCriteriaCheck.enter(self._wf_control, self._application)

        elif event.editor_group is not None:
            eg = EditorGroup.pull(event.editor_group)
            if eg is None:
                raise ValueError(f"EditorGroup '{event.editor_group}' does not exist")

            wfc.editor_group = eg.name
            del wfc.reviewer

            return QuickFailAwaitingAssignment.enter(self._wf_control, self._application)

        raise ValueError("Triaged event must have either a target maned or a target editor group")

    def event_unclaim(self, event: Unclaim):
        wfc = self.workflow_control
        if wfc.reviewer != event.actor_id:
            raise AuthoriseException(reason=AuthoriseException.NOT_AUTHORISED)

        del wfc.reviewer
        return AwaitingTriage.enter(self._wf_control, self._application)

    def event_reassign(self, event: Reassign):
        wfc = self.workflow_control
        if not event.actor.has_role(constants.ROLE_ADMIN):
            raise AuthoriseException(reason=AuthoriseException.WRONG_ROLE)

        wfc.reviewer = event.reviewer_id
        return self.enter(self._wf_control, self._application)

    def event_fail(self, event: Fail):
        # TODO: we don't know where this goes yet
        raise NotImplementedError()

    def event_rescind_minimal_review(self, event: RescindMinimalReview):
        wfc = self.workflow_control
        if wfc.reviewer != event.actor_id:
            raise AuthoriseException(reason=AuthoriseException.NOT_AUTHORISED)

        wfc.triage.has_minimal_review = False
        return TriageAssessmentInProgress.enter(self._wf_control, self._application)

    def do_edit(self, action: ApplicationEdit):
        wfc = self.workflow_control
        if wfc.reviewer != action.actor_id:
            raise AuthoriseException(reason=AuthoriseException.NOT_AUTHORISED)

        # FIXME: where does has_minimal_review get calculated?
        if self.workflow_control.triage.has_minimal_review:
            return self
        else:
            return self.event_rescind_minimal_review(RescindMinimalReview(action.actor_id))


class QuickFailAwaitingAssignment(State):
    pass

class QuickFailCriteriaCheck(State):
    pass


class WorkflowService:
    STATES = [
        # Triage States
        AwaitingTriage,
        TriageAssessmentInProgress,
        TriageAssessmentMinimalReview,

        # Quick Fail States
        QuickFailAwaitingAssignment,
        QuickFailCriteriaCheck
    ]

    def iterate_state(self, state:Type[State]):
        query = state.query()
        for wfc in models.WorkflowControl.iterate_unstable(q=query.query()):
            yield state(wfc)

    def first_n_in_state(self, state:Type[State], n:int) -> list[State]:
        query = state.query()
        query.size = n
        return [state(x) for x in models.WorkflowControl.object_query(q=query.query())]

    def apply_event(self, wfc_id:str, event:WorkflowEvent, save=True):
        state_instance = self.state_for_workflow_control(wfc_id)
        if state_instance is None:
            raise ValueError(f"No state found for workflow control with id '{wfc_id}'")

        new_state = self.event(state_instance, event)
        if save:
            new_state.saveall()
        return new_state

    def state_for_workflow_control(self, wfc_id:str) -> Union[State, None]:
        wfc = models.WorkflowControl.pull(wfc_id)
        if wfc is None:
            return None

        for state in self.STATES:
            if state.matches(wfc):
                return state(wfc)

        return None

    def event(self, state_instance:State, event:WorkflowEvent) -> State:
        if event.__class__ not in state_instance.events:
            raise ValueError(f"Invalid event '{event}' for state '{type(state_instance).__name__}'")

        new_state = state_instance.exit(event)
        return new_state

    def initialise_workflow(self, application):
        wfc = models.WorkflowControl()
        wfc.application_id = application.id
        wfc.original_application = application
        wfc.application_title = application.bibjson().title
        initial_state = AwaitingTriage.enter(wfc, application)
        return initial_state