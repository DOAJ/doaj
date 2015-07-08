from flask import Blueprint, jsonify, url_for, request, make_response, abort, render_template
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
    swag = swagger(app)
    swag['info']['title'] = "DOAJ API documentation"
    swag['info']['description'] = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. In a augue nulla. In vehicula est eget erat iaculis, et lacinia enim faucibus. Aliquam diam dolor, euismod ultrices viverra vitae, congue sit amet massa. Duis vestibulum, quam ut ultrices sagittis, nunc diam cursus odio, sed efficitur eros erat a sapien. Lorem ipsum dolor sit amet, consectetur adipiscing elit. In a augue nulla. In vehicula est eget erat iaculis, et lacinia enim faucibus. Aliquam diam dolor, euismod ultrices viverra vitae, congue sit amet massa. Duis vestibulum, quam ut ultrices sagittis, nunc diam cursus odio, sed efficitur eros erat a sapien. I am fairly sure there is no limit to this, but it is limited to the type of stuff we can put in here because it's all one big string, so no paragrahing or the like, I think. "

    return make_response((jsonify(swag), 200, {'Access-Control-Allow-Origin': '*'}))

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
    return render_template('doaj/api_docs.html')

@blueprint.route('/search/<search_type>/<path:search_query>')
def search(search_type, search_query):
    """
    Search journals and articles
    ---
    tags:
      - search
    description: "Lorem ipsum dolor sit amet, consectetur adipiscing elit. In a augue nulla. In vehicula est eget erat iaculis, et lacinia enim faucibus. Aliquam diam dolor, euismod ultrices viverra vitae, congue sit amet massa. Duis vestibulum, quam ut ultrices sagittis, nunc diam cursus odio, sed efficitur eros erat a sapien."
    parameters:
      -
        name: "search_type"
        description: "lalalalallalala"
        in: "path"
        required: true
        type: "string"
      -
        name: "search_query"
        description: "this is definitely a very useful place to put some description of each parameter"
        in: "path"
        required: true
        type: "string"
      -
        name: "page"
        description: "Lorem ipsum dolor sit amet, consectetur adipiscing elit. In a augue nulla. In vehicula est eget erat iaculis, et lacinia enim faucibus. Aliquam diam dolor, euismod ultrices viverra vitae, congue sit amet massa. Duis vestibulum, quam ut ultrices sagittis, nunc diam cursus odio, sed efficitur eros erat a sapien."
        in: "body"
        required: false
        type: "int"
      -
        name: "pageSize"
        description: "Wooo, we can write small essays in here as well. Again limited as it is a string, but pretty neat"
        in: "body"
        required: false,
        type: "int"
    responses:
      200:
        description: "Search results"
        schema:
            properties:
                company:
                  type: "string"
                description:
                  type: "string"
                rating:
                  type: "number"
                images:
                  type: "array"
                  items:
                    type: "string"
                datetime:
                  type: "number"
                location:
                  type: "string"
      400:
        description: "Bad Request"
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
