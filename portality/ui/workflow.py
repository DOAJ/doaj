from portality.bll.services.workflow.core import Claim, Assign, Reassign, Unclaim, Fail, ApplicationEdit, Unassign
from portality.bll.services.workflow.triage import MinimalReview, RescindMinimalReview, Triaged
from portality.ui import templates
from portality.util import url_for

class StateUI:
    def __init__(self, state):
        self.state = state
        self._events = None
        self._actions = None

    @property
    def workflow_control(self):
        return self.state.workflow_control

    @property
    def events(self):
        if self._events is not None:
            return self._events
        self._events = [EVENT_MAP.get(e) for e in self.state.events if EVENT_MAP.get(e) is not None]
        return self._events

    @property
    def actions(self):
        if self._actions is not None:
            return self._actions
        self._actions = [ACTION_MAP.get(a) for a in self.state.actions if ACTION_MAP.get(a) is not None]
        return self._actions

#################################

class EventUI:
    template = None
    route_id = None

    @classmethod
    def get_route(cls):
        return url_for(cls.route_id)

class ClaimUI(EventUI):
    template = templates.WORKFLOW_CLAIM_WIDGET
    route_id = "workflow.claim"

class AssignUI(EventUI):
    template = templates.WORKFLOW_ASSIGN_WIDGET
    route_id = "workflow.assign"

class UnassignUI(EventUI):
    template = templates.WORKFLOW_UNASSIGN_WIDGET
    route_id = "workflow.unassign"

class UnclaimUI(EventUI):
    template = templates.WORKFLOW_UNCLAIM_WIDGET
    route_id = "workflow.unclaim"

class ReassignUI(EventUI):
    template = templates.WORKFLOW_ASSIGN_WIDGET
    route_id = "workflow.reassign"

class FailUI(EventUI):
    template = templates.WORKFLOW_FAIL_WIDGET
    route_id = "workflow.fail"

class TriagedUI(EventUI):
    template = templates.WORKFLOW_TRIAGED_WIDGET
    route_id = "workflow.triaged"

EVENT_MAP = {
    Claim: ClaimUI,
    Assign: AssignUI,
    Reassign: ReassignUI,
    Unclaim: UnclaimUI,
    Fail: FailUI,
    Unassign: UnassignUI,

    MinimalReview: None,
    RescindMinimalReview: None,
    Triaged: TriagedUI,

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