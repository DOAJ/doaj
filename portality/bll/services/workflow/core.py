from typing import Union

from portality.models import Account, WorkflowControl, Application, WorkflowControlStateQuery

#####################################
## Base Workflow Event and all shared events

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

class Assign(ReviewerAssignment): pass

class Reassign(ReviewerAssignment): pass

class Claim(WorkflowEvent): pass

class Unclaim(WorkflowEvent): pass

class Unassign(WorkflowEvent): pass

class Fail(WorkflowEvent):
    def __init__(self, actor:Union[str, Account], note:str=None, embargo_end:str=None):
        super().__init__(actor)
        self._note = note
        self._embargo_end = embargo_end

    @property
    def note(self):
        return self._note

    @property
    def embargo_end(self):
        return self._embargo_end

#####################################
## Base Workflow Action and all shared actions

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

class ApplicationEdit(WorkflowAction): pass

######################################
## Base State object

class State:
    module = None
    stage = None
    editor_group = None
    reviewer = None

    events = []
    actions = []

    def __init__(self, wf_control:WorkflowControl, application:Application=None):
        self._wf_control = wf_control
        self._application = application

    @classmethod
    def query(cls):
        return WorkflowControlStateQuery(cls.module, cls.stage, cls.editor_group, cls.reviewer)

    @classmethod
    def enter(cls, actor:Union[str, Account],
              wf_control:WorkflowControl,
              application:Application=None,
              from_state: "State"=None):
        instance = cls(wf_control, application)
        instance.apply()
        instance.audit(actor, from_state)
        return instance

    @classmethod
    def matches(cls, wf_control:WorkflowControl):
        # Check the module.
        # If the wfc has no module, and the state definition requires a specific module, then it doesn't match.
        # If the wfc has a module, and the state definition requires a specifc module, and it isn't this one, then it doesn't match
        if wf_control.module is None:
            if not (cls.module == WorkflowControl.ANY):
                return False
        else:
            if not (cls.module == WorkflowControl.ANY or cls.module == wf_control.module):
                return False

        # if we get to here, module matches

        # check the stage
        # If the wfc has no stage, and the state definition requires a specific stage, then it doesn't match.
        # If the wfc has a stage, and the state definition requires a specifc stage, and it isn't this one, then it doesn't match
        if wf_control.stage is None:
            if not (cls.stage == WorkflowControl.ANY):
                return False
        else:
            if not (cls.stage == WorkflowControl.ANY or cls.stage == wf_control.stage):
                return False

        # by here, module and stage match

        # check the editor group
        # if the wfc has no eg, then if the allowed editor group is not WorkflowControl.ANY or WorkflowControl.UNASSIGNED), no match
        # if the wfc has an eg, then if the allowed editor group is not WorkflowControl.ANY or WorkflowControl.ASSIGNED or the same as the wfc's eg, no match
        if wf_control.editor_group is None:
            if not (cls.editor_group == WorkflowControl.ANY or cls.editor_group == WorkflowControl.UNASSIGNED):
                return False
        else:
            if not (cls.editor_group == WorkflowControl.ANY or cls.editor_group == WorkflowControl.ASSIGNED or cls.editor_group == wf_control.editor_group):
                return False

        # by here, module, stage and editor group match

        if wf_control.reviewer is None:
            if not (cls.reviewer == WorkflowControl.ANY or cls.reviewer == WorkflowControl.UNASSIGNED):
                return False
        else:
            if not (cls.reviewer == WorkflowControl.ANY or cls.reviewer == WorkflowControl.ASSIGNED or cls.reviewer == wf_control.editor_group):
                return False

        return True

    @property
    def workflow_control(self):
        return self._wf_control

    @property
    def application(self):
        if self._application is None:
            app_id = self.workflow_control.application_id
            self._application = Application.pull(app_id)
        return self._application

    def apply(self):
        pass

    def exit(self, event:WorkflowEvent):
        return self

    def do(self, action:WorkflowAction):
        return self

    def get_audit_partial(self):
        return {
            "module": self.module,
            "stage": self.stage,
            "editor_group": self.workflow_control.editor_group,
            "reviewer": self.workflow_control.reviewer
        }

    def audit(self, actor, from_state:"State"=None, date=None):
        origin_data = None
        if from_state is not None:
            origin_data = from_state.get_audit_partial()
        target_data = self.get_audit_partial()
        self.workflow_control.add_audit(actor, target_data, origin_data, date)

    def saveall(self, *args, **kwargs):
        self.workflow_control.save(*args, **kwargs)
        if self._application:
            self._application.save(*args, **kwargs)