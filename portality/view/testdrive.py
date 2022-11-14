from flask import Blueprint, make_response, abort
from doajtest.testdrive.factory import TestFactory
from portality import util
from portality.core import app
import json

# ~~Testdrive:Blueprint->$Testdrive:Feature~~
blueprint = Blueprint('testdrive', __name__)

@blueprint.route('/<test_id>')
@util.jsonp
def testdrive(test_id):
    # if not app.config.get("DEBUG", False):
    #     abort(404)
    test = TestFactory.get(test_id)
    if not test:
        abort(404)
    params = test.setup()
    resp = make_response(json.dumps(params))
    resp.mimetype = "application/json"
    return resp