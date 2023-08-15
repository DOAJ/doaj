import json
import re

from flask import Blueprint, request
from flask import jsonify, url_for, make_response, render_template
from flask_login import current_user
from flask_swagger import swagger

from portality.api import respond
from portality.api.common import Api400Error
from portality.api.current import ArticlesBulkApi
from portality.core import app
from portality.decorators import api_key_required, swag, write_required
from portality.lib import plausible
from portality.models import BulkArticles
from portality.view import api_v3

# Google Analytics category for API events
GA_CATEGORY = app.config.get('GA_CATEGORY_API', 'API Hit')
GA_ACTIONS = app.config.get('GA_ACTIONS_API', {})

blueprint = Blueprint('api_v4', __name__)
API_VERSION_NUMBER = '4.0.1'


@blueprint.route("/bulk/articles", methods=["POST"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Bulk article creation asynchronously <span class="red">[Authenticated, not public]</span>',
      swag_spec=ArticlesBulkApi.create_async_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@plausible.pa_event(GA_CATEGORY, action=GA_ACTIONS.get('bulk_article_create_async',
                                                       'Bulk article create asynchronously'))
def bulk_article_create():
    """
    the different compare to v3 is it becomes asynchronously,
    mosly validation will be done in the background task.

    :return:
    """
    data = api_v3._load_income_articles_json(request)
    upload_id = ArticlesBulkApi.create_async(data, current_user._get_current_object())
    resp_content = json.dumps({'msg': 'articles are being created asynchronously',
                               'upload_id': upload_id})
    return respond(resp_content, 202)


@blueprint.route("/bulk/articles/status", methods=["GET"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Get bulk article creation status <span class="red">[Authenticated, not public]</span>',
      swag_spec=ArticlesBulkApi.get_status_swag())
@plausible.pa_event(GA_CATEGORY, action=GA_ACTIONS.get('bulk_article_create_status',
                                                       'Get bulk article creation status'))
def bulk_article_create_status():
    upload_id = request.values.get("upload_id", None)
    if not upload_id:
        raise Api400Error("upload_id is required")

    bulk_article = BulkArticles.pull(upload_id)
    if bulk_article is None or bulk_article.owner != current_user.id:
        raise Api400Error("upload_id is invalid")

    resp_content = json.dumps({
        'status': bulk_article.status,
        'results': {
            "imported": bulk_article.imported,
            "failed": bulk_article.failed_imports,
            "update": bulk_article.updates,
            "new": bulk_article.new,
        },
    })
    return respond(resp_content, 200)


@blueprint.route('/docs')
def docs():
    from portality.view import api_current
    account_url = None
    if current_user.is_authenticated:
        account_url = url_for('account.username', username=current_user.id, _external=True,
                              _scheme=app.config.get('PREFERRED_URL_SCHEME', 'https'))
    return render_template('api/current/api_docs.html',
                           api_version=api_current.LATEST_API_VERSION_NUMBER,
                           base_url=app.config.get("BASE_API_URL", url_for('.api_root')),
                           contact_us_url=url_for('doaj.contact'),
                           account_url=account_url)


@blueprint.route('/swagger.json')
def api_spec():
    from portality.view import api_current
    swag = swagger(app)
    swag['info']['title'] = ""
    swag['info']['version'] = api_current.LATEST_API_VERSION_NUMBER

    # Strip out the duplicate versioned route from the swagger so we only show latest as /api/
    [swag['paths'].pop(p) for p in list(swag['paths'].keys()) if re.match(r'/api/v\d+/', p)]
    return make_response((jsonify(swag), 200, {'Access-Control-Allow-Origin': '*'}))
