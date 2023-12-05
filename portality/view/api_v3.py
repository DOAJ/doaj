import json

from flask import Blueprint, url_for, request
from flask_login import current_user

from portality.api.current import Api400Error, bulk_created
from portality.api.current import ApplicationsCrudApi, ArticlesCrudApi, JournalsCrudApi, ApplicationsBulkApi, \
    ArticlesBulkApi
from portality.api.current import DiscoveryApi
from portality.core import app
from portality.decorators import api_key_required, api_key_optional, swag, write_required
from portality.lib import plausible
from portality.view import api_v4

blueprint = Blueprint('api_v3', __name__)

API_VERSION_NUMBER = '3.0.1'  # OA start added 2022-03-21

# Google Analytics category for API events
ANALYTICS_CATEGORY = app.config.get('ANALYTICS_CATEGORY_API', 'API Hit')
ANALYTICS_ACTIONS = app.config.get('ANALYTICS_ACTIONS_API', {})


@blueprint.route('/')
def api_root():
    return api_v4.api_root()


@blueprint.route('/docs')
def docs():
    return api_v4.docs()


@blueprint.route('/swagger.json')
def api_spec():
    return api_v4.api_spec()

# Handle wayward paths by raising an API404Error
@blueprint.route("/<path:invalid_path>", methods=["POST", "GET", "PUT", "DELETE", "PATCH",
                                                  "HEAD"])  # leaving out methods should mean all, but tests haven't shown that behaviour.
def missing_resource(invalid_path):
    return api_v4.missing_resource(invalid_path)


@swag(swag_summary='Search your applications <span class="red">[Authenticated, not public]</span>',
      swag_spec=DiscoveryApi.get_application_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@blueprint.route("/search/applications/<path:search_query>")
@api_key_required
@plausible.pa_event(ANALYTICS_CATEGORY, action=ANALYTICS_ACTIONS.get('search_applications', 'Search applications'),
                    record_value_of_which_arg='search_query')
def search_applications(search_query):
    return api_v4.search_applications(search_query)


@swag(swag_summary='Search journals',
      swag_spec=DiscoveryApi.get_journal_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@blueprint.route('/search/journals/<path:search_query>')
@plausible.pa_event(ANALYTICS_CATEGORY, action=ANALYTICS_ACTIONS.get('search_journals', 'Search journals'),
                    record_value_of_which_arg='search_query')
def search_journals(search_query):
    return api_v4.search_journals(search_query)


@swag(swag_summary='Search articles',
      swag_spec=DiscoveryApi.get_article_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@blueprint.route('/search/articles/<path:search_query>')
@plausible.pa_event(ANALYTICS_CATEGORY, action=ANALYTICS_ACTIONS.get('search_articles', 'Search articles'),
                    record_value_of_which_arg='search_query')
def search_articles(search_query):
    return api_v4.search_articles(search_query)


#########################################
# Application CRUD API

@blueprint.route("/applications", methods=["POST"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Create an application <span class="red">[Authenticated, not public]</span>',
      swag_spec=ApplicationsCrudApi.create_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@plausible.pa_event(ANALYTICS_CATEGORY, action=ANALYTICS_ACTIONS.get('create_application', 'Create application'))
def create_application():
    return api_v4.create_application()


@blueprint.route("/applications/<application_id>", methods=["GET"])
@api_key_required
@swag(swag_summary='Retrieve an application <span class="red">[Authenticated, not public]</span>',
      swag_spec=ApplicationsCrudApi.retrieve_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@plausible.pa_event(ANALYTICS_CATEGORY, action=ANALYTICS_ACTIONS.get('retrieve_application', 'Retrieve application'),
                    record_value_of_which_arg='application_id')
def retrieve_application(application_id):
    return api_v4.retrieve_application(application_id)


@blueprint.route("/applications/<application_id>", methods=["PUT"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Update an application <span class="red">[Authenticated, not public]</span>',
      swag_spec=ApplicationsCrudApi.update_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@plausible.pa_event(ANALYTICS_CATEGORY, action=ANALYTICS_ACTIONS.get('update_application', 'Update application'),
                    record_value_of_which_arg='application_id')
def update_application(application_id):
    return api_v4.update_application(application_id)


@blueprint.route("/applications/<application_id>", methods=["DELETE"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Delete an application <span class="red">[Authenticated, not public]</span>',
      swag_spec=ApplicationsCrudApi.delete_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@plausible.pa_event(ANALYTICS_CATEGORY, action=ANALYTICS_ACTIONS.get('delete_application', 'Delete application'),
                    record_value_of_which_arg='application_id')
def delete_application(application_id):
    return api_v4.delete_application(application_id)


#########################################
# Article CRUD API

@blueprint.route("/articles", methods=["POST"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Create an article <span class="red">[Authenticated, not public]</span>',
      swag_spec=ArticlesCrudApi.create_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@plausible.pa_event(ANALYTICS_CATEGORY, action=ANALYTICS_ACTIONS.get('create_article', 'Create article'))
def create_article():
    return api_v4.create_article()


@blueprint.route("/articles/<article_id>", methods=["GET"])
@api_key_optional
@swag(swag_summary='Retrieve an article',
      swag_spec=ArticlesCrudApi.retrieve_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@plausible.pa_event(ANALYTICS_CATEGORY, action=ANALYTICS_ACTIONS.get('retrieve_article', 'Retrieve article'),
                    record_value_of_which_arg='article_id')
def retrieve_article(article_id):
    return api_v4.retrieve_article(article_id)


@blueprint.route("/articles/<article_id>", methods=["PUT"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Update an article <span class="red">[Authenticated, not public]</span>',
      swag_spec=ArticlesCrudApi.update_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@plausible.pa_event(ANALYTICS_CATEGORY, action=ANALYTICS_ACTIONS.get('update_article', 'Update article'),
                    record_value_of_which_arg='article_id')
def update_article(article_id):
    return api_v4.update_article(article_id)


@blueprint.route("/articles/<article_id>", methods=["DELETE"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Delete an article <span class="red">[Authenticated, not public]</span>',
      swag_spec=ArticlesCrudApi.delete_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@plausible.pa_event(ANALYTICS_CATEGORY, action=ANALYTICS_ACTIONS.get('delete_article', 'Delete article'),
                    record_value_of_which_arg='article_id')
def delete_article(article_id):
    return api_v4.delete_article(article_id)


#########################################
# Journal R API

@blueprint.route('/journals/<journal_id>', methods=['GET'])
@api_key_optional
@swag(swag_summary='Retrieve a journal by ID',
      swag_spec=JournalsCrudApi.retrieve_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@plausible.pa_event(ANALYTICS_CATEGORY, action=ANALYTICS_ACTIONS.get('retrieve_journal', 'Retrieve journal'),
                    record_value_of_which_arg='journal_id')
def retrieve_journal(journal_id):
    return api_v4.retrieve_journal(journal_id)


#########################################
# Application Bulk API

@blueprint.route("/bulk/applications", methods=["POST"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Create applications in bulk <span class="red">[Authenticated, not public]</span>',
      swag_spec=ApplicationsBulkApi.create_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@plausible.pa_event(ANALYTICS_CATEGORY, action=ANALYTICS_ACTIONS.get('bulk_application_create', 'Bulk application create'))
def bulk_application_create():
    return api_v4.bulk_application_create()


@blueprint.route("/bulk/applications", methods=["DELETE"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Delete applications in bulk <span class="red">[Authenticated, not public]</span>',
      swag_spec=ApplicationsBulkApi.delete_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@plausible.pa_event(ANALYTICS_CATEGORY, action=ANALYTICS_ACTIONS.get('bulk_application_delete', 'Bulk application delete'))
def bulk_application_delete():
    return api_v4.bulk_application_delete()


#########################################
# Article Bulk API

def _load_income_articles_json(request):
    # get the data from the request
    try:
        return json.loads(request.data.decode("utf-8"))
    except:
        raise Api400Error("Supplied data was not valid JSON")


@blueprint.route("/bulk/articles", methods=["POST"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Bulk article creation <span class="red">[Authenticated, not public]</span>',
      swag_spec=ArticlesBulkApi.create_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@plausible.pa_event(ANALYTICS_CATEGORY, action=ANALYTICS_ACTIONS.get('bulk_article_create', 'Bulk article create'))
def bulk_article_create():
    data = _load_income_articles_json(request)

    # delegate to the API implementation
    ids = ArticlesBulkApi.create(data, current_user._get_current_object())

    # get all the locations for the ids
    inl = []
    for id in ids:
        inl.append((id, url_for("api_v3.retrieve_article", article_id=id)))

    # respond with a suitable Created response
    return bulk_created(inl)


@blueprint.route("/bulk/articles", methods=["DELETE"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Bulk article delete <span class="red">[Authenticated, not public]</span>',
      swag_spec=ArticlesBulkApi.delete_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@plausible.pa_event(ANALYTICS_CATEGORY, action=ANALYTICS_ACTIONS.get('bulk_article_delete', 'Bulk article delete'))
def bulk_article_delete():
    return api_v4.bulk_article_delete()
