import json

from flask import Blueprint, render_template, request, abort, url_for, redirect, make_response
from flask_login import login_required, current_user

from portality import models
from portality.bll import DOAJ
from portality.bll.exceptions import AuthoriseException
from portality.bll.services.workflow import AwaitingTriage, TriageAssessmentInProgress, Claim, Unclaim, \
    TriageAssessmentMinimalReview, MinimalReview, RescindMinimalReview
from portality.decorators import ssl_required
from portality.ui import templates
from portality.ui.workflow import StateUI

blueprint = Blueprint('workflow', __name__)

@blueprint.route('/')
@login_required
@ssl_required
def index():
    svc = DOAJ.workflowService()
    awaiting_triage = [StateUI(x) for x in svc.first_n_in_state(AwaitingTriage, 10)]
    triage_in_progress = [StateUI(x) for x in svc.first_n_in_state(TriageAssessmentInProgress, 10)]
    triage_minimal_review = [StateUI(x) for x in svc.first_n_in_state(TriageAssessmentMinimalReview, 10)]
    return render_template(templates.ADMIN_WORKFLOW_OVERVIEW,
                           awaiting_triage=awaiting_triage,
                           triage_in_progress=triage_in_progress,
                           triage_minimal_review=triage_minimal_review,
                           admin_page=True)

@blueprint.route('/claim', methods=['POST'])
@login_required
@ssl_required
def claim():
    wfc_id = request.form.get("workflow_control")
    if wfc_id is None:
        abort(400)

    svc = DOAJ.workflowService()
    try:
        new_state = svc.apply_event(wfc_id, Claim(current_user))
    except AuthoriseException:
        abort(401)
    except ValueError:
        abort(404)

    onward = request.form.get("onward")
    if onward is not None:
        url = url_for(onward)
        return redirect(url)

    resp = make_response(json.dumps({"status": "success"}))
    resp.mimetype = "application/json"
    return resp

@blueprint.route("/unclaim", methods=["POST"])
@login_required
@ssl_required
def unclaim():
    wfc_id = request.form.get("workflow_control")
    if wfc_id is None:
        abort(400)

    svc = DOAJ.workflowService()
    try:
        new_state = svc.apply_event(wfc_id, Unclaim(current_user))
    except AuthoriseException:
        abort(401)
    except ValueError:
        abort(404)

    onward = request.form.get("onward")
    if onward is not None:
        url = url_for(onward)
        return redirect(url)

    resp = make_response(json.dumps({"status": "success"}))
    resp.mimetype = "application/json"
    return resp

@blueprint.route("/assign", methods=["POST"])
@login_required
@ssl_required
def assign():
    pass

@blueprint.route("/reassign", methods=["POST"])
@login_required
@ssl_required
def reassign():
    pass

@blueprint.route("/fail", methods=["POST"])
@login_required
@ssl_required
def fail():
    pass

@blueprint.route("/minimal_review", methods=["POST"])
@login_required
@ssl_required
def minimal_review():
    pass

@blueprint.route("/triaged", methods=["POST"])
@login_required
@ssl_required
def triaged():
    pass

@blueprint.route("/edit/<application_id>", methods=["GET"])
@login_required
@ssl_required
def edit(application_id):
    # FIXME: this is just a demonstrator
    try:
        wfc = models.WorkflowControl.find_by_application(application_id)
    except ValueError:
        abort(500)

    if wfc is None:
        abort(404)

    event = None
    if wfc.triage.has_minimal_review:
        event = RescindMinimalReview(current_user)
    else:
        event = MinimalReview(current_user)

    svc = DOAJ.workflowService()
    try:
        new_state = svc.apply_event(wfc.id, event)
    except AuthoriseException:
        abort(401)
    except ValueError:
        abort(404)

    url = url_for("workflow.index")
    return redirect(url)

