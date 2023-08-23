import json
import yaml
import os

from flask import Blueprint, make_response, request, abort
from portality.core import app
from portality.bll import DOAJ

blueprint = Blueprint('tours', __name__)

@blueprint.route('/<content_id>', methods=['GET'])
def tour(content_id=None):
    tourdir = os.path.join(app.config["BASE_FILE_PATH"], "..", "cms", "tours")
    tourpath = os.path.join(tourdir, content_id + ".yml")
    with open(tourpath) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)

    idx = 0
    for d in data.get("steps"):
        idx += 1
        d["step"] = idx

    resp = make_response(json.dumps(data.get("steps", [])))
    resp.mimetype = "application/json"
    return resp

@blueprint.route("/<content_id>/seen", methods=["GET"])
def tour_seen(content_id=None):
    tourSvc = DOAJ.tourService()
    if not tourSvc.validateContentId(content_id):
        abort(404)

    resp = make_response()
    cookie_key = app.config.get("TOUR_COOKIE_PREFIX") + content_id
    cookie_value = content_id
    max_age = app.config.get("TOUR_COOKIE_MAX_AGE")
    resp.set_cookie(cookie_key, cookie_value, max_age=max_age, samesite=None, secure=True)
    return resp