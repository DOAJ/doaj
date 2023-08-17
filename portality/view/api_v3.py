from flask import Blueprint, url_for, request
from flask_login import current_user

from portality.api.current import ArticlesBulkApi
from portality.api.current import bulk_created
from portality.core import app
from portality.decorators import api_key_required, swag, write_required
from portality.lib import plausible
from portality.view import api_v4

blueprint = Blueprint('api_v3', __name__)

API_VERSION_NUMBER = '3.0.1'  # OA start added 2022-03-21

# Google Analytics category for API events
GA_CATEGORY = app.config.get('GA_CATEGORY_API', 'API Hit')
GA_ACTIONS = app.config.get('GA_ACTIONS_API', {})

blueprint.route('/')(api_v4.api_root)
blueprint.route('/docs')(api_v4.docs)
blueprint.route('/swagger.json')(api_v4.api_spec)

# Handle wayward paths by raising an API404Error
# leaving out methods should mean all, but tests haven't shown that behaviour.
(blueprint.route
 ("/<path:invalid_path>", methods=["POST", "GET", "PUT", "DELETE", "PATCH", "HEAD"])
 (api_v4.missing_resource)
 )

(blueprint.route
 ("/search/applications/<path:search_query>")
 (api_v4.search_applications)
 )

blueprint.route('/search/journals/<path:search_query>')(api_v4.search_journals)
blueprint.route('/search/articles/<path:search_query>')(api_v4.search_articles)

#########################################
# Application CRUD API

blueprint.route("/applications", methods=["POST"])(api_v4.create_application)
blueprint.route("/applications/<application_id>", methods=["GET"])(api_v4.retrieve_application)
blueprint.route("/applications/<application_id>", methods=["PUT"])(api_v4.update_application)
blueprint.route("/applications/<application_id>", methods=["DELETE"])(api_v4.delete_application)

#########################################
# Article CRUD API

blueprint.route("/articles", methods=["POST"])(api_v4.create_article)
blueprint.route("/articles/<article_id>", methods=["GET"])(api_v4.retrieve_article)
blueprint.route("/articles/<article_id>", methods=["PUT"])(api_v4.update_article)
blueprint.route("/articles/<article_id>", methods=["DELETE"])(api_v4.delete_article)

#########################################
# Journal R API
blueprint.route('/journals/<journal_id>', methods=['GET'])(api_v4.retrieve_journal)

#########################################
# Application Bulk API

blueprint.route("/bulk/applications", methods=["POST"])(api_v4.bulk_application_create)
blueprint.route("/bulk/applications", methods=["DELETE"])(api_v4.bulk_application_delete)


#########################################
# Article Bulk API


@blueprint.route("/bulk/articles", methods=["POST"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Bulk article creation <span class="red">[Authenticated, not public]</span>',
      swag_spec=ArticlesBulkApi.create_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@plausible.pa_event(GA_CATEGORY, action=GA_ACTIONS.get('bulk_article_create', 'Bulk article create'))
def bulk_article_create():
    data = api_v4.load_income_articles_json(request)

    # delegate to the API implementation
    ids = ArticlesBulkApi.create(data, current_user._get_current_object())

    # get all the locations for the ids
    inl = []
    for id in ids:
        inl.append((id, url_for("api_v3.retrieve_article", article_id=id)))

    # respond with a suitable Created response
    return bulk_created(inl)


blueprint.route("/bulk/articles", methods=["DELETE"])(api_v4.bulk_article_delete)
