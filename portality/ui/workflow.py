from enum import Enum

from portality.bll.services.workflow.core import Claim, Assign, Reassign, Unclaim, Fail, ApplicationEdit, Unassign, \
    State
from portality.bll.services.workflow.triage import MinimalReview, RescindMinimalReview, Triaged, MODULE_TRIAGE
from portality.ui import templates
from portality.util import url_for

class StateUI:
    def __init__(self, state):
        self.state = state
        self._events = None
        self._actions = None

    def assignable_users(self):
        return self.state.assignable_users()

    @property
    def workflow_control(self):
        return self.state.workflow_control

    @property
    def application(self):
        return self.state.application

    @property
    def events(self):
        raise NotImplementedError()

    @property
    def actions(self):
        if self._actions is not None:
            return self._actions
        self._actions = [ACTION_MAP.get(a) for a in self.state.actions if ACTION_MAP.get(a) is not None]
        return self._actions

class EventUI:
    template = None
    route_id = None
    user_roles = None
    user_attributes = None

    @classmethod
    def get_route(cls):
        return url_for(cls.route_id)

    @classmethod
    def is_available(cls, account):
        if cls.user_roles is not None:
            if not any([account.has_role(r) for r in cls.user_roles]):
                return False
        if cls.user_attributes is not None:
            if not any([account.has_attribute(t, v) for t, v in cls.user_attributes]):
                return False
        return True

#########################################
## Triage Module UI

class TriageStateUI(StateUI):
    @property
    def events(self):
        if self._events is not None:
            return self._events
        self._events = [TRIAGE_EVENT_MAP.get(e) for e in self.state.events if TRIAGE_EVENT_MAP.get(e) is not None]
        return self._events

    def _event_by_class(self, event_class):
        for event in self.events:
            if event == event_class:
                return event
        return None

    @property
    def event_claim(self):
        return self._event_by_class(TriageClaimUI)

    @property
    def event_assign(self):
        return self._event_by_class(TriageAssignUI)

    @property
    def event_unassign(self):
        return self._event_by_class(TriageUnassignUI)

    @property
    def event_unclaim(self):
        return self._event_by_class(TriageUnclaimUI)

    @property
    def event_reassign(self):
        return self._event_by_class(TriageReassignUI)

    @property
    def event_reject(self):
        return self._event_by_class(TriageFailUI)

    @property
    def event_triaged(self):
        return self._event_by_class(TriageTriagedUI)


class TriageClaimUI(EventUI):
    template = templates.WORKFLOW_TRIAGE_CLAIM_WIDGET
    route_id = "workflow.claim"
    outcome_route_id = "workflow.triage_form"

class TriageAssignUI(EventUI):
    template = templates.WORKFLOW_GENERIC_ASSIGN_WIDGET
    route_id = "workflow.assign"

class TriageUnassignUI(EventUI):
    template = templates.WORKFLOW_GENERIC_UNASSIGN_WIDGET
    route_id = "workflow.unassign"

class TriageUnclaimUI(EventUI):
    template = templates.WORKFLOW_UNCLAIM_WIDGET
    route_id = "workflow.unclaim"

class TriageReassignUI(EventUI):
    template = templates.WORKFLOW_GENERIC_ASSIGN_WIDGET
    route_id = "workflow.reassign"

class TriageFailUI(EventUI):
    template = templates.WORKFLOW_FAIL_WIDGET
    route_id = "workflow.fail"

class TriageTriagedUI(EventUI):
    template = templates.WORKFLOW_TRIAGED_WIDGET
    route_id = "workflow.triaged"

TRIAGE_EVENT_MAP = {
    Claim: TriageClaimUI,
    Assign: TriageAssignUI,
    Reassign: TriageReassignUI,
    Unclaim: TriageUnclaimUI,
    Fail: TriageFailUI,
    Unassign: TriageUnassignUI,

    MinimalReview: None,
    RescindMinimalReview: None,
    Triaged: TriageTriagedUI,

}

#####################################

class ActionUI:
    template = None
    route_id = None

    @classmethod
    def get_route(cls, *args, **kwargs):
        return url_for(cls.route_id, *args, **kwargs)

class ApplicationEditUI(ActionUI):
    template = templates.WORKFLOW_EDIT_WIDGET
    route_id = "workflow.edit"

ACTION_MAP = {
    ApplicationEdit: ApplicationEditUI
}

##########################################
## Factory

class Modules:
    TRIAGE = MODULE_TRIAGE

class StateUIFactory:
    @classmethod
    def get(cls, state):
        module = state.workflow_control.module
        match module:
            case Modules.TRIAGE:
                return TriageStateUI(state)
        return None