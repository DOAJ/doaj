import importlib

from flask import Blueprint, make_response, abort, url_for, request, render_template, jsonify
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

    if request.values.get("json"):
        resp = make_response(json.dumps(params))
        resp.mimetype = "application/json"
        return resp

    return render_template("dev/testdrive/testdrive.html", params=params, name=test_id)


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

@blueprint.route('/run', methods=['GET', 'POST'])
@util.jsonp
@login_required
def run_script():
    data = request.get_json()
    script_name = data.get('script_name')
    if script_name not in app.config.get("TESTDRIVE_SCRIPT_WHITELIST"):
        return jsonify({'error': 'Invalid script'}), 400
    module = importlib.import_module(f'portality.scripts.{script_name}')
    module.main()
    return jsonify({'status': 'success', 'received': script_name})