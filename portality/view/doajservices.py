import json

from flask import Blueprint, abort, make_response
from flask.ext.login import current_user, login_required

from portality.core import app, ssl_required

from portality import lock

blueprint = Blueprint('doajservices', __name__)

@blueprint.route("/unlock/<object_type>/<object_id>", methods=["POST"])
@login_required
@ssl_required
def unlock(object_type, object_id):
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
    resp = make_response(json.dumps({"result" : "success"}))
    resp.mimetype = "application/json"
    return resp