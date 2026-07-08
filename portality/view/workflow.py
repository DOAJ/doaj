import json
from copy import deepcopy

from flask import Blueprint, render_template, request, abort, url_for, redirect, make_response, flash
from flask_login import login_required, current_user

from portality import models, constants
from portality.bll import DOAJ
from portality.bll.exceptions import AuthoriseException
from portality.bll.services.workflow.core import Claim, Unclaim, Unassign, Fail, Assign, Reassign
from portality.bll.services.workflow.rejected import Rejected
from portality.bll.services.workflow.triage import AwaitingTriage, TriageAssessmentInProgress, \
    TriageAssessmentMinimalReview, RescindMinimalReview, MinimalReview
from portality.decorators import ssl_required, write_required, restrict_to_role
from portality.forms.workflow.triage.processors import TriageFormProcessor
from portality.lib import dicts
from portality.ui import templates
from portality.ui.workflow import StateUIFactory

blueprint = Blueprint('workflow', __name__)

# restrict everything in workflow to logged in users with the "admin" role
@blueprint.before_request
def restrict():
    return restrict_to_role(constants.ROLE_ADMIN)

@blueprint.route('/')
@login_required
@ssl_required
def index():
    svc = DOAJ.workflowService()
    awaiting_triage = [StateUIFactory.get(x) for x in svc.first_n_in_state(AwaitingTriage, 10)]
    triage_in_progress = [StateUIFactory.get(x) for x in svc.first_n_in_state(TriageAssessmentInProgress, 10)]
    triage_minimal_review = [StateUIFactory.get(x) for x in svc.first_n_in_state(TriageAssessmentMinimalReview, 10)]
    rejected = [StateUIFactory.get(x) for x in svc.first_n_in_state(Rejected, 10)]
    return render_template(templates.ADMIN_WORKFLOW_OVERVIEW,
                           awaiting_triage=awaiting_triage,
                           triage_in_progress=triage_in_progress,
                           triage_minimal_review=triage_minimal_review,
                           rejected=rejected,
                           admin_page=True)

@blueprint.route('/search', methods=['GET'])
@login_required
@ssl_required
def workflow_search():
    return render_template(templates.WORKFLOW_SEARCH)

@blueprint.route('/overview/<application_id>', methods=['GET'])
@login_required
@ssl_required
@write_required()
def workflow_item_overview(application_id):
    svc = DOAJ.workflowService()
    state = svc.state_for_application(application_id)
    ui = StateUIFactory.get(state)
    return render_template(templates.WORKFLOW_ITEM_OVERVIEW, state=ui)

@blueprint.route("/triage-form/<application_id>", methods=["GET", "POST"])
@login_required
@ssl_required
@write_required()
def triage_form(application_id):
    if not (current_user.is_super or current_user.has_attribute(constants.USER_ATTR__WORKFLOW, constants.EWF__TRIAGE)):
        abort(403)

    application = models.Application.pull(application_id)
    if application is None:
        abort(404)

    # NOTE: this hack lets us `pull` the worfklow control object, avoiding any re-indexing
    # latency when redirecting to this page after a save
    wfc_id = request.values.get("wfc")
    if wfc_id is not None:
        wfc = models.WorkflowControl.pull(wfc_id)
        if wfc.application_id != application_id:
            abort(400)
    else:
        wfc = models.WorkflowControl.find_by_application(application_id)
    if wfc is None:
        abort(404)

    if request.method == "GET":
        processor = TriageFormProcessor(source_application=application, source_wfc=wfc)
        form_html = processor.render_form()
        return render_template(templates.WORKFLOW_TRIAGE_PAGE, form_html=form_html, application=application, wfc=wfc)

    elif request.method == "POST":
        formdata = dicts.multidict_2_dict(request.form)
        processor = TriageFormProcessor(source_application=application, source_wfc=wfc, raw_formdata=formdata)
        valid = processor.validate()
        if valid:
            try:
                processor.finalise(current_user._get_current_object())
            except AuthoriseException:
                abort(401)

            flash("Record updated")
            return redirect(url_for("workflow.triage_form", application_id=application.id, wfc=wfc.id))
        else:
            form_html = processor.render_form()
            return render_template(templates.WORKFLOW_TRIAGE_PAGE, form_html=form_html, application=application,
                                   wfc=wfc)

@blueprint.route("/triage-form/<application_id>/async/<wfc_id>", methods=["POST"])
@login_required
@ssl_required
@write_required()
def triage_form_async(application_id, wfc_id):
    if not (current_user.is_super or current_user.has_attribute(constants.USER_ATTR__WORKFLOW, constants.EWF__TRIAGE)):
        abort(403)

    application = models.Application.pull(application_id)
    if application is None:
        abort(404)

    wfc = models.WorkflowControl.pull(wfc_id)
    if wfc.application_id != application_id:
        abort(400)

    formdata = dicts.multidict_2_dict(request.form)
    processor = TriageFormProcessor(source_application=application, source_wfc=wfc, raw_formdata=formdata)
    valid = processor.validate()
    if valid:
        try:
            processor.finalise(current_user._get_current_object())
        except AuthoriseException:
            abort(401)

        recommendation = processor.recommendation()
        resp = make_response(json.dumps({"recommendation": recommendation}))
        resp.mimetype = "application/json"
        return resp

    else:
        validation_messages = processor.validation_report()
        resp = make_response(json.dumps({"validation": validation_messages}))
        resp.mimetype = "application/json"
        return resp

####################################
## Workflow actions

def _apply_event(wfc_id, event, async_request, onward_url):
    if wfc_id is None:
        abort(400)

    args = {}
    if not event.actor:
        event.actor = current_user

    svc = DOAJ.workflowService()
    try:
        new_state = svc.apply_event(wfc_id, event)
    except AuthoriseException:
        abort(401)
    except ValueError:
        abort(400)

    if async_request:
        resp = make_response(json.dumps({"new_state": new_state.__class__.__name__}))
        resp.mimetype = "application/json"
        return resp

    if onward_url:
        return redirect(onward_url)

@blueprint.route('/claim', methods=['POST'])
@login_required
@ssl_required
def claim():
    wfc_id = request.form.get("workflow_control")
    app_id = request.form.get("application")
    async_request = request.form.get("async") == "y"
    onward = request.form.get("onward")
    if onward:
        onward = url_for(onward, application_id=app_id, wfc=wfc_id)
    return _apply_event(wfc_id, Claim(current_user), async_request, onward)

@blueprint.route("/unclaim", methods=["POST"])
@login_required
@ssl_required
def unclaim():
    wfc_id = request.form.get("workflow_control")
    app_id = request.form.get("application")
    async_request = request.form.get("async") == "y"
    onward = request.form.get("onward")
    if onward:
        onward = url_for(onward, application_id=app_id, wfc=wfc_id)
    return _apply_event(wfc_id, Unclaim(current_user), async_request, onward)

@blueprint.route("/assign", methods=["POST"])
@login_required
@ssl_required
def assign():
    wfc_id = request.form.get("workflow_control")
    app_id = request.form.get("application")
    async_request = request.form.get("async") == "y"
    onward = request.form.get("onward")
    assign_to = request.form.get("assign_to")

    if not assign_to:
        abort(400)

    if onward:
        onward = url_for(onward, application_id=app_id, wfc=wfc_id)
    return _apply_event(wfc_id, Assign(current_user, assign_to), async_request, onward)

@blueprint.route("/reassign", methods=["POST"])
@login_required
@ssl_required
def reassign():
    wfc_id = request.form.get("workflow_control")
    app_id = request.form.get("application")
    async_request = request.form.get("async") == "y"
    onward = request.form.get("onward")
    assign_to = request.form.get("assign_to")

    if not assign_to:
        abort(400)

    if onward:
        onward = url_for(onward, application_id=app_id, wfc=wfc_id)
    return _apply_event(wfc_id, Reassign(current_user, assign_to), async_request, onward)

@blueprint.route("/unassign", methods=["POST"])
@login_required
@ssl_required
def unassign():
    wfc_id = request.form.get("workflow_control")
    app_id = request.form.get("application")
    async_request = request.form.get("async") == "y"
    onward = request.form.get("onward")
    if onward:
        onward = url_for(onward, application_id=app_id, wfc=wfc_id)
    return _apply_event(wfc_id, Unassign(current_user), async_request, onward)

@blueprint.route("/fail", methods=["POST"])
@login_required
@ssl_required
def fail():
    wfc_id = request.form.get("workflow_control")
    onward = request.form.get("onward")
    note = request.form.get("note")
    embargo = request.form.get("embargo_end")

    return _apply_event(wfc_id, Fail, onward, event_args={"note": note, "embargo_end": embargo})

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
    if wfc.triage.review_complete:
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


