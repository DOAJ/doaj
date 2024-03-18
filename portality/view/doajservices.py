import json
from urllib.parse import urlparse

from flask import Blueprint, make_response, request, abort, render_template
from flask_login import current_user, login_required

from portality import lock, models
from portality.bll import DOAJ
from portality.core import app
from portality.decorators import ssl_required, write_required
from portality.lib import urlshort, plausible
from portality.util import jsonp

blueprint = Blueprint('doajservices', __name__)


@blueprint.route("/unlock/<object_type>/<object_id>", methods=["POST"])
@login_required
@ssl_required
@write_required()
def unlock(object_type, object_id):
    # change from suggestion to application after redesign, that needs refactoring to make the code consistent
    # that if is only for quick hotfix to make sure the functionality works
    if object_type == "application":
        object_type = "suggestion"

    # first figure out if we are allowed to even contemplate this action
    if object_type not in ["journal", "suggestion"]:
        abort(404)
    if object_type == "journal":
        if not current_user.has_role("edit_journal"):
            abort(401)
    if object_type == "suggestion":
        if not current_user.has_role("edit_suggestion"):
            abort(401)

    # try to unlock
    unlocked = lock.unlock(object_type, object_id, current_user.id)

    # if we couldn't unlock, this is a bad request
    if not unlocked:
        abort(400)

    # otherwise, return success
    resp = make_response(json.dumps({"result": "success"}))
    resp.mimetype = "application/json"
    return resp


@blueprint.route("/unlocked")
@login_required
def unlocked():
    """
    Redirect to this route on completion of an unlock
    :return:
    """
    return render_template("unlocked.html")


@blueprint.route("/shorten", methods=["POST"])
@plausible.pa_event(app.config.get('ANALYTICS_CATEGORY_URLSHORT', 'Urlshort'),
                    action=app.config.get('ANALYTICS_ACTION_URLSHORT_ADD', 'Find or create shortener url'))
def shorten():
    """ create shortener url """
    data = json.loads(request.data)
    url = data['url']

    # validate url
    path = urlparse(url).path
    if not any(path == p for p in app.config.get("ALLOWED_SHORTEN_PATH", [])):
        app.logger.warning(f"Invalid url shorten request: {url}")
        abort(400)

    short_url = urlshort.add_url_shortener(url)
    resp = make_response(json.dumps({"short_url": short_url}))
    resp.mimetype = "application/json"
    return resp


@blueprint.route("/groupstatus/<group_id>", methods=["GET"])
@jsonp
@login_required
def group_status(group_id):
    """
    ~~GroupStatus:Feature -> Todo:Service~~
    :param group_id:
    :return:
    """
    if (not (current_user.has_role("editor") and models.EditorGroup.pull(group_id).editor == current_user.id)) and (
            not current_user.has_role("admin")):
        abort(404)
    svc = DOAJ.todoService()
    stats = svc.group_stats(group_id)
    return make_response(json.dumps(stats))


@blueprint.route("/autocheck/dismiss/<autocheck_set_id>/<autocheck_id>", methods=["GET", "POST"])
@jsonp
@login_required
def dismiss_autocheck(autocheck_set_id, autocheck_id):
    if not current_user.has_role("admin"):
        abort(404)
    svc = DOAJ.autochecksService()
    done = svc.dismiss(autocheck_set_id, autocheck_id)
    if not done:
        abort(404)
    return make_response(json.dumps({"status": "success"}))

@blueprint.route("/autocheck/undismiss/<autocheck_set_id>/<autocheck_id>", methods=["GET", "POST"])
@jsonp
@login_required
def undismiss_autocheck(autocheck_set_id, autocheck_id):
    if not current_user.has_role("admin"):
        abort(404)
    svc = DOAJ.autochecksService()
    done = svc.undismiss(autocheck_set_id, autocheck_id)
    if not done:
        abort(404)
    return make_response(json.dumps({"status": "success"}))

