from flask import Blueprint, jsonify, url_for, request, make_response, abort
from flask_swagger import swagger

from portality.api.v1 import DiscoveryApi, DiscoveryException, jsonify_models
from portality.core import app

import json

blueprint = Blueprint('api_v1', __name__)

def _bad_request(message=None, exception=None):
    if exception is not None:
        message = exception.message
    app.logger.info("Sending 400 Bad Request from client: {x}".format(x=message))
    resp = make_response(json.dumps({"status" : "error", "error" : message}))
    resp.mimetype = "application/json"
    resp.status_code = 400
    return resp

@blueprint.route('/spec')
def api_spec():
    return make_response((jsonify(swagger(app)), 200, {'Access-Control-Allow-Origin': '*'}))

@blueprint.route('/')
def list_operations():
    # todo use reflection or something
    return jsonify({'available_operations': [
        {
            'description': "Search for journals and articles",
            'base_url': request.base_url + 'search',
            'docs_url': url_for('.docs', _anchor='search', _external=True)
        }
    ]})

@blueprint.route('/docs')
def docs():
    return 'Documentation root'

@blueprint.route('/search/<search_type>/<path:search_query>')
def search(search_type, search_query):
    """
    Search journals and articles
    ---
    tags:
      - search
    description: "Search DOAJ journals and articles"
    parameters:
      -
        name: "search_type"
        in: "path"
        required: true
        type: "string"
      -
        name: "search_query"
        in: "path"
        required: true
        type: "string"
      -
        name: "page"
        in: "body":
        required: false
        type: "int"
      -
        name: "pageSize"
        in: "body"
        required: false,
        type: "int"
    responses:
      200:
        description: Search results
      400:
        description: Bad Request
    """
    # get the values for the 2 other bits of search info: the page number and the page size
    page = request.values.get("page", 1)
    psize = request.values.get("pageSize", 10)

    # check the page is an integer
    try:
        page = int(page)
    except:
        return _bad_request("Page number was not an integer")

    # check the page size is an integer
    try:
        psize = int(psize)
    except:
        return _bad_request("Page size was not an integer")

    results = None
    if search_type == "articles":
        try:
            results = DiscoveryApi.search_articles(search_query, page, psize)
        except DiscoveryException as e:
            return _bad_request(e.message)
    elif search_type == "journals":
        try:
            results = DiscoveryApi.search_journals(search_query, page, psize)
        except DiscoveryException as e:
            return _bad_request(e.message)
    else:
        abort(404)

    return jsonify_models(results)