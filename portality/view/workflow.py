import json
from asyncore import write
from copy import deepcopy

from flask import Blueprint, render_template, request, abort, url_for, redirect, make_response, flash
from flask_login import login_required, current_user
from formulaic.serialise.form.core import FormSerialiser, FormDataParser

from portality import models, constants
from portality.bll import DOAJ
from portality.bll.exceptions import AuthoriseException
from portality.bll.services.workflow.core import Claim, Unclaim, Unassign, Fail
from portality.bll.services.workflow.rejected import Rejected
from portality.bll.services.workflow.triage import AwaitingTriage, TriageAssessmentInProgress, \
    TriageAssessmentMinimalReview, RescindMinimalReview, MinimalReview
from portality.decorators import ssl_required, write_required
from portality.forms.workflow.crosswalk import WorkflowControl2TriageForm, TriageForm2WorkflowControl
from portality.forms.workflow.triage.forms import TriageForm
from portality.forms.workflow.triage.processors import TriageFormProcessor
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
    rejected = [StateUI(x) for x in svc.first_n_in_state(Rejected, 10)]
    return render_template(templates.ADMIN_WORKFLOW_OVERVIEW,
                           awaiting_triage=awaiting_triage,
                           triage_in_progress=triage_in_progress,
                           triage_minimal_review=triage_minimal_review,
                           rejected=rejected,
                           admin_page=True)

def _apply_event(wfc_id, event_class, onward_route, event_args:dict=None):
    if wfc_id is None:
        abort(400)

    args = {}
    if event_args is not None:
        args = deepcopy(event_args)
    args["actor"] = current_user

    svc = DOAJ.workflowService()
    try:
        new_state = svc.apply_event(wfc_id, event_class(**args))
    except AuthoriseException:
        abort(401)
    except ValueError:
        abort(400)

    if onward_route is not None:
        url = url_for(onward_route)
        return redirect(url)

    resp = make_response(json.dumps({"new_state": new_state.__class__.__name__}))
    resp.mimetype = "application/json"
    return resp

@blueprint.route('/claim', methods=['POST'])
@login_required
@ssl_required
def claim():
    wfc_id = request.form.get("workflow_control")
    onward = request.form.get("onward")
    return _apply_event(wfc_id, Claim, onward)

@blueprint.route("/unclaim", methods=["POST"])
@login_required
@ssl_required
def unclaim():
    wfc_id = request.form.get("workflow_control")
    onward = request.form.get("onward")
    return _apply_event(wfc_id, Unclaim, onward)

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

@blueprint.route("/unassign", methods=["POST"])
@login_required
@ssl_required
def unassign():
    wfc_id = request.form.get("workflow_control")
    onward = request.form.get("onward")
    return _apply_event(wfc_id, Unassign, onward)

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
        # form_html = processor.render_form()
        # xwalk = WorkflowControl2TriageForm()
        # formdata = xwalk.transform(wfc, application)
        #
        # serialiser = FormSerialiser()
        # form_html = serialiser.data_to_string(formdata, TriageForm(), application=application, wfc=wfc)

        return render_template(templates.WORKFLOW_PAGE_TRIAGE, form_html=form_html, application=application, wfc=wfc)

    elif request.method == "POST":
        processor = TriageFormProcessor(source_application=application, source_wfc=wfc, raw_formdata=request.form)
        processor.process_raw_form(current_user._get_current_object())
        processor.finalise(current_user._get_current_object())

        flash("Record updated")
        return redirect(url_for("workflow.triage_form", application_id=application.id, wfc=wfc.id))
        # form = request.form
        # parser = FormDataParser()
        # formdata = parser.representation_to_data(form, TriageForm())
        # xwalk = TriageForm2WorkflowControl()
        # partial_wfc, partial_application = xwalk.transform(formdata)

