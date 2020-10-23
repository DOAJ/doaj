import json, urllib.request, urllib.parse, urllib.error, requests

from flask import Blueprint, make_response, request, abort
from flask_login import current_user, login_required

from portality.core import app
from portality.decorators import ssl_required, write_required
from portality.util import jsonp
from portality import lock

blueprint = Blueprint('doajservices', __name__)


@blueprint.route("/unlock/<object_type>/<object_id>", methods=["POST"])
@login_required
@ssl_required
@write_required()
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


@blueprint.route("/shorten", methods=["POST"])
@jsonp
def shorten():
    # Enable this if you are testing and you want to see the front end work, without working bit.ly credentials
    # return make_response(json.dumps({"url" : "testing url"}))
    try:
        # parse the json
        d = json.loads(request.data)
        p = d['page']
        q = d['query']

        # re-serialise the query, and url encode it
        source = urllib.parse.quote(json.dumps(q))

        # assemble the DOAJ url
        doajurl = p + "?source=" + source

        # assemble the bitly url.  Note that we re-encode the doajurl to include in the
        # query arguments, so by this point it is double-encoded
        bitly = app.config.get("BITLY_SHORTENING_API_URL")
        bitly_oauth = app.config.get("BITLY_OAUTH_TOKEN")

        # Set an Auth Bearer token (Bitly 4.0)
        headers = {'Authorization': 'Bearer ' + bitly_oauth}

        # Add the long url as a payload
        payload = {'long_url': doajurl}

        # make the request
        resp = requests.post(bitly, headers=headers, data=json.dumps(payload))
        shorturl = resp.json().get('link')

        if not shorturl:
            abort(400)

        # make the response
        answer = make_response(json.dumps({"url": shorturl}))
        answer.mimetype = "application/json"
        return answer
    except:
        abort(400)
