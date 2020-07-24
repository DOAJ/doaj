import json

from flask import Blueprint, render_template, abort, redirect, url_for, request, make_response
from flask_login import current_user

from portality import models
from portality.decorators import write_required

from portality.forms.application_forms import ApplicationFormFactory

blueprint = Blueprint('apply', __name__)


@blueprint.route("/", methods=["GET", "POST"])
@write_required()
def public_application(draft_id=None):

    if not current_user.is_authenticated:
        return redirect(url_for("account.login",  redirected="apply"))

    draft_application = None
    if draft_id is not None:
        draft_application = models.DraftApplication.pull(draft_id)
        if draft_application is None:
            abort(404)
        if draft_application.owner != current_user.id:
            abort(404)

    if request.method == "GET":
        fc = ApplicationFormFactory.context("public")
        if draft_application is not None:
            fc.processor(source=draft_application)
        return fc.render_template(obj=draft_application)

    elif request.method == "POST":

        print("submitting")

        fc = ApplicationFormFactory.context("public")

        draft = request.form.get("draft")
        async_def = request.form.get("async")
        draft_id = request.form.get("draft_id")

        if draft_id != "new_form":
            draft_application = models.DraftApplication.pull(draft_id)
            if draft_application is None:
                abort(404)
            if draft_application.owner != current_user.id:
                abort(404)

        processor = fc.processor(formdata=request.form)

        if draft == "false":
            if processor.validate():
                processor.finalise()
                return redirect(url_for('doaj.application_thanks', _anchor='thanks'))
            else:
                return fc.render_template()

        else:
            the_draft = processor.draft(current_user._get_current_object(), id=draft_id)
            if async_def is not None:
                return make_response(json.dumps({"id": the_draft.id}), 200)
            else:
                return redirect(url_for('doaj.application_thanks', _anchor='draft'))
