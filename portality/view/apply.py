import json

from flask import Blueprint, render_template, abort, redirect, url_for, request, make_response
from flask_login import current_user

from portality import models
from portality.decorators import write_required

from portality.forms.application_forms import ApplicationFormFactory

blueprint = Blueprint('apply', __name__)


@blueprint.route("/thank-you", methods=["GET"])
def application_thanks():
    return render_template("layouts/static_page.html", page_frag="/apply/thank-you-fragment/index.html", page_title="Thank you")


@blueprint.route("/draft", methods=["GET"])
def draft_saved():
    return render_template("layouts/static_page.html", page_frag="doaj/draft_saved.html", page_title="Draft saved")


@blueprint.route("/", methods=["GET", "POST"])
@blueprint.route("/<draft_id>", methods=["GET", "POST"])
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

        fc = ApplicationFormFactory.context("public")

        draft = request.form.get("draft")
        async_def = request.form.get("async")
        if draft_id is None:
            draft_id = request.form.get("id")

        if draft_id is not None and draft_application is None:
            draft_application = models.DraftApplication.pull(draft_id)
            if draft_application is None:
                abort(404)
            if draft_application.owner != current_user.id:
                abort(404)

        processor = fc.processor(formdata=request.form)

        if draft == "true":
            the_draft = processor.draft(current_user._get_current_object(), id=draft_id)
            if async_def is not None:
                return make_response(json.dumps({"id": the_draft.id}), 200)
            else:
                return redirect(url_for('apply.draft_saved'))
        else:
            if processor.validate():
                processor.finalise(current_user._get_current_object())
                return redirect(url_for('apply.application_thanks', _anchor='thanks'))
            else:
                return fc.render_template()
