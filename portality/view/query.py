import json, urllib.request, urllib.error, urllib.parse

from flask import Blueprint, request, abort, make_response
from flask_login import current_user

from portality import util
from portality.bll.doaj import DOAJ
from portality.bll import exceptions

blueprint = Blueprint('query', __name__)

# pass queries direct to index. POST only for receipt of complex query objects
@blueprint.route('/<path:path>', methods=['GET','POST'])
@util.jsonp
def query(path=None):
    """
    Query endpoint for general queries via the web interface.  Calls on the DOAJ.queryService for action

    :param path:
    :return:
    """
    pathparts = request.path.strip('/').split('/')
    if len(pathparts) < 2:
        abort(400)
    domain = pathparts[0]
    index_type = pathparts[1]

    q = None
    # if this is a POST, read the contents out of the body
    if request.method == "POST":
        q = request.json
    # if there is a source param, load the json from it
    elif 'source' in request.values:
        q = json.loads(urllib.parse.unquote(request.values['source']))

    try:
        account = None
        if current_user is not None and not current_user.is_anonymous:
            account = current_user._get_current_object()
        queryService = DOAJ.queryService()
        res = queryService.search(domain, index_type, q, account, request.values)
    except exceptions.AuthoriseException as e:
        abort(403)
    except exceptions.NoSuchObjectException as e:
        abort(404)

    resp = make_response(json.dumps(res))
    resp.mimetype = "application/json"
    return resp
