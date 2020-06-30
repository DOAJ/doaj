from flask import Blueprint, make_response
from flask_login import current_user, login_required
from flask import abort
from portality.decorators import api_key_required

from portality import models as models
from portality import constants
from portality.crosswalks.jct_inprogress import JCTInProgressXWalk

import json

blueprint = Blueprint('jct', __name__)

INCLUDE_STATUSES = [
    constants.APPLICATION_STATUS_COMPLETED,
    constants.APPLICATION_STATUS_IN_PROGRESS,
    constants.APPLICATION_STATUS_READY,
    constants.APPLICATION_STATUS_REVISIONS_REQUIRED,
    constants.APPLICATION_STATUS_UPDATE_REQUEST
]

@blueprint.route('/inprogress')
@api_key_required
def inprogress():
    if not current_user.has_role("jct_inprogress"):
        abort(404)

    records = []
    for application in models.Suggestion.list_by_status(INCLUDE_STATUSES):
        record = JCTInProgressXWalk.application2jct(application)
        records.append(record)

    data = json.dumps(records)
    return make_response((data, 200, {'Content-Type': 'application/json'}))
