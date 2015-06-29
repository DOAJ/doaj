from flask import Blueprint, jsonify, url_for, request, make_response
from flask_swagger import swagger

from portality.api.v1 import DiscoveryApi, jsonify_models
from portality.core import app

blueprint = Blueprint('api_v1', __name__)

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

@blueprint.route('/search/<search_type>/<search_query>')
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
    responses:
      200:
        description: Search results
    """
    results = {
        'results': {
            'search_query': search_query,
        }
    }

    if search_type == 'articles' or search_type == 'all':
        results['results'].update({'articles': DiscoveryApi.search_articles(search_query)})

    if search_type == 'journals' or search_type == 'all':
        results['results'].update({'journals': DiscoveryApi.search_journals(search_query)})

    return jsonify_models(results)