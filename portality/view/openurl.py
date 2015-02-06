from flask import Blueprint, request

blueprint = Blueprint('openurl', __name__)

@blueprint.route("/openurl", methods=["GET", "POST"])
def get_incoming_query():
    url_query = request.url.split(request.base_url).pop()
    return url_query

