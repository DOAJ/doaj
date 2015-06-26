from flask import Blueprint, jsonify, url_for, request, make_response

blueprint = Blueprint('api_v1', __name__)

@blueprint.route('/')
def list_operations():
    # todo use reflection or something
    return jsonify({'available_operations': [
        {
            'description': "Search for journals and articles",
            'url': url_for('.search', _external=True),
            'docs_url': url_for('.docs', _anchor='search', _external=True)
        }
    ]})

@blueprint.route('/docs')
def docs():
    return 'Documentation root'

@blueprint.route('/search')
def search():
    """
    Search journals and articles
    ---
    tags:
      - search
    parameters:
      - in: body
        name: query
        schema:
          id: query
          required:
            - q
          properties:
            q:
              type: string
              description: search query
    responses:
      200:
        description: Search results
    """
    if not request.args.get('q'):
        return make_response((jsonify({'error': 'Missing "q" search query parameter. Append ?q=your%20url%20encoded%20search%20query to your request.'}), 400))

    return jsonify(
        {
            'results': {
                'search_query': request.args['q'],
                'articles': [{'id': '1ef4de', 'title': 'Mock article 1'}, {'id': '1ef4ff', 'title': 'Mock article 2'}],
                'journals': [{'id': '2ef4de', 'title': 'Mock journal 1'}, {'id': '2ef4ff', 'title': 'Mock journal 2'}]
            }
        }
    )