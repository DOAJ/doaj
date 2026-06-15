"""
DO NOT EDIT THIS TEST DIRECTLY.

Use the stub in matrices/triage_workflow and regenerate using generate_tests.py
"""

from portality import constants
from portality.bll import DOAJ
from portality.bll.exceptions import AuthoriseException
from portality.bll.services.workflow.core import ApplicationEdit, Claim, Assign, Unclaim, Unassign, Reassign, Fail, \
    WorkflowEvent
from portality.bll.services.workflow.triage import MinimalReview, RescindMinimalReview, Triaged
from portality.lib import dates
from portality.models import WorkflowControl, Account, Application
from doajtest.fixtures import AccountFixtureFactory, ApplicationFixtureFactory


def reviewer_factory(reviewer_def):
    if reviewer_def == "none":
        return None

    if reviewer_def == "triage":
        editor = Account(**AccountFixtureFactory.make_editor_source())
        editor.add_attribute(constants.USER_ATTR__WORKFLOW, constants.EWF__TRIAGE)
        editor.set_id(editor.makeid())
        return editor

    if reviewer_def == "non_triage":
        editor = Account(**AccountFixtureFactory.make_editor_source())
        editor.set_id(editor.makeid())
        return editor

    raise ValueError(f"Unknown reviewer definition '{reviewer_def}'")

def actor_factory(actor_def, wfc):
    if actor_def == "assigned_triage":
        acc = reviewer_factory("triage")
        acc.set_id(wfc.reviewer_id)
        return acc

    if actor_def == "assigned_non_triage":
        acc = reviewer_factory("non_triage")
        acc.set_id(wfc.reviewer_id)
        return acc

    if actor_def == "admin":
        acc = Account(**AccountFixtureFactory.make_managing_editor_source())
        acc.set_id(acc.makeid())
        return acc

    if actor_def == "unassigned_triage":
        acc = reviewer_factory("triage")
        acc.set_id(acc.makeid())
        return acc

    if actor_def == "unassigned_non_triage":
        acc = reviewer_factory("non_triage")
        acc.set_id(acc.makeid())
        return acc

    raise ValueError(f"Unknown actor definition '{actor_def}'")

def label_factory(label_def):
    if label_def == "none":
        return None

    if label_def == "quick_fail":
        return constants.EWF__QUICK_FAIL

    if label_def == "quality_review":
        return constants.EWF__QUALITY_REVIEW

    raise ValueError(f"Unknown label definition '{label_def}'")

def action_factory(action_def, actor, label):
    if action_def == "action_edit":
        return ApplicationEdit(actor)
    if action_def == "event_claim":
        return Claim(actor)
    if action_def == "event_assign_triage":
        new_assignee = reviewer_factory("triage")
        return Assign(actor, new_assignee)
    if action_def == "event_assign_non_triage":
        new_assignee = reviewer_factory("non_triage")
        return Assign(actor, new_assignee)
    if action_def == "event_unclaim":
        return Unclaim(actor)
    if action_def == "event_unassign":
        return Unassign(actor)
    if action_def == "event_reassign_triage":
        new_assignee = reviewer_factory("triage")
        return Reassign(actor, new_assignee)
    if action_def == "event_reassign_non_triage":
        new_assignee = reviewer_factory("non_triage")
        return Reassign(actor, new_assignee)
    if action_def == "event_minimal_review":
        return MinimalReview(actor)
    if action_def == "event_fail":
        return Fail(actor, "A note", dates.days_after_now(180))
    if action_def == "event_rescind_minimal_review":
        return RescindMinimalReview(actor)
    if action_def == "event_triaged":
        return Triaged(actor, label)

    raise ValueError(f"Unknown action definition '{action_def}'")

def hmr_factory(hmr_def):
    if hmr_def == "yes":
        return True

    if hmr_def == "no":
        return False

    raise ValueError(f"Unknown hmr definition '{hmr_def}'")

def error_factory(error_def):
    if error_def == "no":
        return None
    if error_def == "AuthoriseException":
        return AuthoriseException

    raise ValueError(f"Unknown error definition '{error_def}'")

def result_reviewer_factory(rr_def):
    if rr_def == "none":
        return False
    if rr_def == "assigned":
        return True
    if rr_def == "":
        return None

    raise ValueError(f"Unknown result reviewer definition '{rr_def}'")

def editor_group_factory(eg_def):
    if eg_def == "none":
        return None
    return eg_def

def run_test(kwargs):
    module = kwargs.get("module")
    stage = kwargs.get("stage")
    reviewer_arg = kwargs.get("reviewer")
    action = kwargs.get("action")
    actor_arg = kwargs.get("actor")
    has_minimal_review = kwargs.get("has_minimal_review")
    label_arg = kwargs.get("label")
    result_module = kwargs.get("result_module")
    result_stage = kwargs.get("result_stage")
    result_reviewer_arg = kwargs.get("result_reviewer")
    initial_legacy_status = kwargs.get("initial_legacy_status")
    result_legacy_status = kwargs.get("result_legacy_status")
    initial_legacy_eg = kwargs.get("initial_legacy_eg")
    result_legacy_eg = kwargs.get("result_legacy_eg")
    error = kwargs.get("error")

    reviewer = reviewer_factory(reviewer_arg)
    label = label_factory(label_arg)
    has_minimal_review = hmr_factory(has_minimal_review)
    expected_error = error_factory(error)
    has_reviewer_at_end = result_reviewer_factory(result_reviewer_arg)
    result_editor_group = editor_group_factory(result_legacy_eg)

    application = Application(**ApplicationFixtureFactory.make_application_source({
        "id": Application.makeid()
    }))

    wfc = WorkflowControl()
    wfc.module = module
    wfc.stage = stage
    if reviewer is not None:
        wfc.reviewer_id = reviewer.id
        wfc._reviewer_object = reviewer # a bit cheeky, just to avoid index lookups
    wfc.triage.has_minimal_review = has_minimal_review
    wfc.application_id = application.id
    wfc.set_id(wfc.makeid())

    actor = actor_factory(actor_arg, wfc)
    action = action_factory(action, actor, label)

    svc = DOAJ.workflowService()
    state = svc.state_for_workflow_control(wfc, application)

    # in order to apply initial conditions, we also need to "enter" the state, which we can do by
    # apply()ing the state's constraints
    state.apply()

    assert state is not None
    assert state.application.application_status == initial_legacy_status
    assert state.application.editor_group == initial_legacy_eg

    if expected_error is not None:
        try:
            if isinstance(action, WorkflowEvent):
                new_state = state.exit(action)
            else:
                new_state = state.do(action)
        except expected_error:
            pass
        else:
            raise AssertionError(f"Expected {expected_error} to be raised")
        return

    if isinstance(action, WorkflowEvent):
        new_state = state.exit(action)
    else:
        new_state = state.do(action)

    assert new_state.module == result_module

    if result_stage != "":
        assert new_state.stage == result_stage

    if has_reviewer_at_end is not None:
        assert (new_state.workflow_control.reviewer_id is not None) == has_reviewer_at_end

    assert new_state.application.application_status == result_legacy_status

    if result_editor_group is not None:
        assert new_state.application.editor_group == result_editor_group
    else:
        assert new_state.application.editor_group is None

