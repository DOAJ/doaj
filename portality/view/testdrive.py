from flask import Blueprint, make_response, abort, url_for, request
from flask_login import current_user, login_required
from doajtest.testdrive.factory import TestFactory
from portality import util
from portality.core import app
import json
from urllib import parse

# ~~Testdrive:Blueprint->$Testdrive:Feature~~
blueprint = Blueprint('testdrive', __name__)

@blueprint.route('/<test_id>')
@util.jsonp
@login_required
def testdrive(test_id):
    # if not app.config.get("DEBUG", False):
    #     abort(404)
    test = TestFactory.get(test_id)
    if not test:
        abort(404)
    params = test.setup()
    teardown = app.config.get("BASE_URL") + url_for("testdrive.teardown", test_id=test_id) + "?d=" + parse.quote_plus(json.dumps(params))
    params["teardown"] = teardown
    resp = make_response(json.dumps(params))
    resp.mimetype = "application/json"
    return resp


@blueprint.route("/<test_id>/teardown")
@util.jsonp
@login_required
def teardown(test_id):
    test = TestFactory.get(test_id)
    if not test:
        abort(404)
    result = test.teardown(json.loads(request.values.get("d")))
    resp = make_response(json.dumps(result))
    resp.mimetype = "application/json"
    return resp