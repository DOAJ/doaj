import json

from flask import Blueprint, render_template, abort, redirect, url_for, request, make_response
from flask_login import current_user

from portality import models
from portality.decorators import write_required

from portality.forms.application_forms import ApplicationFormFactory

blueprint = Blueprint('apply', __name__)


@blueprint.route("/", methods=["GET", "POST"])
@blueprint.route("/01-oa-compliance/", methods=["GET", "POST"])
@blueprint.route("/02-about/", methods=["GET", "POST"])
@blueprint.route("/03-copyright-licensing/", methods=["GET", "POST"])
@blueprint.route("/04-editorial/", methods=["GET", "POST"])
@blueprint.route("/05-business-model/", methods=["GET", "POST"])
@write_required()
def public_application(draft_id=None):

    if not current_user.is_authenticated:
        return redirect(url_for("account.login",  redirected="apply"))

    if request.path == "/apply/":
        return redirect("/apply/01-oa-compliance/")

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

        # find out if we're being asked to modify the form, rather than submit it
        for key in request.form.keys():
            if key.startswith("field__add"):
                val = request.form.get(key)
                processor = fc.processor(formdata=request.form)
                field = fc.get(val)
                wtf = field.wtfield
                wtf.append_entry()
                return fc.render_template()
            elif key.startswith("field__remove"):
                val = request.form.get(key)

        draft = request.form.get("draft")
        async_def = request.form.get("async")
        draft_id = request.form.get("id") if draft_id is None else draft_id

        if draft_id is not None:
            draft_application = models.DraftApplication.pull(draft_id)
            if draft_application is None:
                abort(404)
            if draft_application.owner != current_user.id:
                abort(404)

        processor = fc.processor(formdata=request.form)

        if draft is not None:
            the_draft = processor.draft(current_user._get_current_object(), id=draft_id)
            if async_def is not None:
                return make_response(json.dumps({"id" : the_draft.id}), 200)
            else:
                return redirect(url_for('doaj.suggestion_thanks', _anchor='draft'))

        else:
            if processor.validate():
                processor.finalise()
                return redirect(url_for('doaj.suggestion_thanks', _anchor='thanks'))
            else:
                return fc.render_template()
