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
    reviewer = None

    legacy_application_status = None
    legacy_editor_group = None

    events = []
    actions = []

    def __init__(self, wf_control:WorkflowControl, application:Application=None):
        self._wf_control = wf_control
        self._application = application

    @classmethod
    def query(cls):
        return WorkflowControlStateQuery(cls.module, cls.stage, cls.reviewer)

    @classmethod
    def enter(cls, actor:Union[str, Account],
              wf_control:WorkflowControl,
              application:Application=None,
              from_state: "State"=None):
        instance = cls(wf_control, application)
        instance.apply()
        instance.audit(actor)
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

        if wf_control.reviewer_id is None:
            if not (cls.reviewer == WorkflowControl.ANY or cls.reviewer == WorkflowControl.UNASSIGNED):
                return False
        else:
            if not (cls.reviewer == WorkflowControl.ANY or cls.reviewer == WorkflowControl.ASSIGNED or cls.reviewer == wf_control.reviewer_id):
                return False

        return True

    @property
    def workflow_control(self) -> WorkflowControl:
        return self._wf_control

    @property
    def application(self):
        if self._application is None:
            app_id = self.workflow_control.application_id
            self._application = Application.pull(app_id)
        return self._application

    ########################################
    ## methods applied at state entry by enter()

    def apply_module(self):
        if self.module is not None and self.module not in WorkflowControl.META_STATES:
            if self.workflow_control.module != self.module:
                self.workflow_control.module = self.module

    def apply_stage(self):
        if self.stage is not None and self.stage not in WorkflowControl.META_STATES:
            if self.workflow_control.stage != self.stage:
                self.workflow_control.stage = self.stage

    def apply_reviewer(self):
        if self.workflow_control.reviewer_id is None and self.reviewer == WorkflowControl.ASSIGNED:
            raise ValueError(f"Reviewer must be set for '{type(self).__name__}' state")

        if self.workflow_control.reviewer_id is not None and self.reviewer == WorkflowControl.UNASSIGNED:
            del self.workflow_control.reviewer_id

    def apply_legacy_application_status(self):
        # back-compatibility for the original workflow
        if self.legacy_application_status is not None:
            application = self.application
            if application.application_status != self.legacy_application_status:
                application.set_application_status(self.legacy_application_status)

    def apply_legacy_application_reviewer(self):
        # back-compatibility for the original workflow
        application = self.application
        application.set_editor_group(self.legacy_editor_group)
        if self.workflow_control.reviewer_id is not None:
            if application.editor != self.workflow_control.reviewer_id:
                application.set_editor(self.workflow_control.reviewer_id)
        else:
            application.remove_editor()

    def apply(self):
        # apply all the appropriate workflow state properties
        self.apply_module()
        self.apply_stage()
        self.apply_reviewer()

        # take the state properties, and propagate any back-compatibility changes to the old workflow
        self.apply_legacy_application_status()
        self.apply_legacy_application_reviewer()

    ##########################################

    def transition(self, target_class, actor):
        return target_class.enter(actor, self._wf_control, self._application, self)

    def exit(self, event:WorkflowEvent):
        return self

    def dispatch_event(self, event: WorkflowEvent, handlers: dict):
        """Dispatch an event to the appropriate handler based on isinstance checks.

        handlers: mapping of EventClass -> handler callable
        """
        for ev_cls, handler in handlers.items():
            if isinstance(event, ev_cls):
                return handler(event)
        raise ValueError(f"Unknown event '{event}' for state '{type(self).__name__}'")

    def do(self, action:WorkflowAction):
        return self

    def get_audit_record(self):
        return {
            "module": self.module,
            "stage": self.stage,
            "reviewer": self.workflow_control.reviewer_id
        }

    def audit(self, actor, date=None):
        target_data = self.get_audit_record()
        self.workflow_control.add_audit(actor, target_data, date)

    def saveall(self, *args, **kwargs):
        self.workflow_control.save(*args, **kwargs)
        if self._application:
            self._application.save(*args, **kwargs)