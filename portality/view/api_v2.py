from flask import Blueprint, jsonify, url_for, request, make_response, abort, render_template, redirect
from flask_login import current_user

from flask_swagger import swagger

from portality.api.v2 import DiscoveryApi, DiscoveryException
from portality.api.v2 import ApplicationsCrudApi, ArticlesCrudApi, JournalsCrudApi, ApplicationsBulkApi, ArticlesBulkApi
from portality.api.v2 import jsonify_models, jsonify_data_object, Api400Error, Api401Error, Api404Error, created, no_content, bulk_created
from portality.core import app
from portality.decorators import api_key_required, api_key_optional, swag, write_required
from portality.lib import analytics
import json

blueprint = Blueprint('api_v2', __name__)

API_VERSION_NUMBER = '2.0.0'

# Google Analytics category for API events
GA_CATEGORY = app.config.get('GA_CATEGORY_API', 'API Hit')
GA_ACTIONS = app.config.get('GA_ACTIONS_API', {})


@blueprint.route('/')
def api_v2_root():
    return redirect(url_for('.api_spec'))


@blueprint.route('/swagger.json')
def api_spec():
    swag = swagger(app)
    swag['info']['title'] = "DOAJ API documentation"

    # Generate the swagger description from the Jinja template
    account_url = None
    if current_user.is_authenticated:
        account_url = url_for('account.username', username=current_user.id, _external=True, _scheme=app.config.get('PREFERRED_URL_SCHEME', 'https'))

    swag['info']['description'] = render_template('api/v2/swagger_description.html',
                                                  api_version=API_VERSION_NUMBER,
                                                  base_url=url_for('.api_v2_root', _external=True, _scheme=app.config.get('PREFERRED_URL_SCHEME', 'https')),
                                                  contact_us_url=url_for('doaj.contact'),
                                                  account_url=account_url)
    swag['info']['version'] = API_VERSION_NUMBER

    return make_response((jsonify(swag), 200, {'Access-Control-Allow-Origin': '*'}))


# Handle wayward paths by raising an API404Error
@blueprint.route("/<path:invalid_path>", methods=["POST", "GET", "PUT", "DELETE", "PATCH", "HEAD"])     # leaving out methods should mean all, but tests haven't shown that behaviour.
def missing_resource(invalid_path):
    docs_url = app.config.get("BASE_URL", "") + url_for('.docs')
    spec_url = app.config.get("BASE_URL", "") + url_for('.api_spec')
    raise Api404Error("No endpoint at {0}. See {1} for valid paths or read the documentation at {2}.".format(invalid_path, spec_url, docs_url))


@blueprint.route('/docs')
def docs():
    return render_template('api/v2/api_docs.html')

@swag(swag_summary='Search your applications <span class="red">[Authenticated, not public]</span>', swag_spec=DiscoveryApi.get_application_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@blueprint.route("/search/applications/<path:search_query>")
@api_key_required
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('search_applications', 'Search applications'), record_value_of_which_arg='search_query')
def search_applications(search_query):
    # get the values for the 2 other bits of search info: the page number and the page size
    page = request.values.get("page", 1)
    psize = request.values.get("pageSize", 10)
    sort = request.values.get("sort")

    # check the page is an integer
    try:
        page = int(page)
    except:
        raise Api400Error("Page number was not an integer")

    # check the page size is an integer
    try:
        psize = int(psize)
    except:
        raise Api400Error("Page size was not an integer")

    try:
        results = DiscoveryApi.search('application', current_user, search_query, page, psize, sort)
    except DiscoveryException as e:
        raise Api400Error(str(e))

    return jsonify_models(results)


@swag(swag_summary='Search journals', swag_spec=DiscoveryApi.get_journal_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@blueprint.route('/search/journals/<path:search_query>')
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('search_journals', 'Search journals'), record_value_of_which_arg='search_query')
def search_journals(search_query):
    # get the values for the 2 other bits of search info: the page number and the page size
    page = request.values.get("page", 1)
    psize = request.values.get("pageSize", 10)
    sort = request.values.get("sort")

    # check the page is an integer
    try:
        page = int(page)
    except:
        raise Api400Error("Page number was not an integer")

    # check the page size is an integer
    try:
        psize = int(psize)
    except:
        raise Api400Error("Page size was not an integer")

    try:
        results = DiscoveryApi.search('journal', None, search_query, page, psize, sort)
    except DiscoveryException as e:
        raise Api400Error(str(e))

    return jsonify_models(results)


@swag(swag_summary='Search articles', swag_spec=DiscoveryApi.get_article_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@blueprint.route('/search/articles/<path:search_query>')
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('search_articles', 'Search articles'), record_value_of_which_arg='search_query')
def search_articles(search_query):
    # get the values for the 2 other bits of search info: the page number and the page size
    page = request.values.get("page", 1)
    psize = request.values.get("pageSize", 10)
    sort = request.values.get("sort")

    # check the page is an integer
    try:
        page = int(page)
    except:
        raise Api400Error("Page number was not an integer")

    # check the page size is an integer
    try:
        psize = int(psize)
    except:
        raise Api400Error("Page size was not an integer")

    results = None
    try:
        results = DiscoveryApi.search('article', None, search_query, page, psize, sort)
    except DiscoveryException as e:
        raise Api400Error(str(e))

    return jsonify_models(results)


#########################################
# Application CRUD API

@blueprint.route("/applications", methods=["POST"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Create an application <span class="red">[Authenticated, not public]</span>', swag_spec=ApplicationsCrudApi.create_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('create_application', 'Create application'))
def create_application():
    # get the data from the request
    try:
        data = json.loads(request.data.decode("utf-8"))
    except:
        raise Api400Error("Supplied data was not valid JSON")

    # delegate to the API implementation
    a = ApplicationsCrudApi.create(data, current_user._get_current_object())

    # respond with a suitable Created response
    return created(a, url_for("api_v2.retrieve_application", application_id=a.id))


@blueprint.route("/applications/<application_id>", methods=["GET"])
@api_key_required
@swag(swag_summary='Retrieve an application <span class="red">[Authenticated, not public]</span>', swag_spec=ApplicationsCrudApi.retrieve_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('retrieve_application', 'Retrieve application'), record_value_of_which_arg='application_id')
def retrieve_application(application_id):
    a = ApplicationsCrudApi.retrieve(application_id, current_user)
    return jsonify_models(a)


@blueprint.route("/applications/<application_id>", methods=["PUT"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Update an application <span class="red">[Authenticated, not public]</span>', swag_spec=ApplicationsCrudApi.update_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('update_application', 'Update application'), record_value_of_which_arg='application_id')
def update_application(application_id):
    # get the data from the request
    try:
        data = json.loads(request.data.decode("utf-8"))
    except:
        raise Api400Error("Supplied data was not valid JSON")

    # delegate to the API implementation
    ApplicationsCrudApi.update(application_id, data, current_user._get_current_object())

    # respond with a suitable No Content successful response
    return no_content()


@blueprint.route("/applications/<application_id>", methods=["DELETE"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Delete an application <span class="red">[Authenticated, not public]</span>', swag_spec=ApplicationsCrudApi.delete_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('delete_application', 'Delete application'), record_value_of_which_arg='application_id')
def delete_application(application_id):
    ApplicationsCrudApi.delete(application_id, current_user._get_current_object())
    return no_content()


#########################################
# Article CRUD API

@blueprint.route("/articles", methods=["POST"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Create an article <span class="red">[Authenticated, not public]</span>', swag_spec=ArticlesCrudApi.create_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('create_article', 'Create article'))
def create_article():
    # get the data from the request
    try:
        data = json.loads(request.data.decode("utf-8"))
    except:
        raise Api400Error("Supplied data was not valid JSON")

    # delegate to the API implementation
    a = ArticlesCrudApi.create(data, current_user._get_current_object())

    # respond with a suitable Created response
    return created(a, url_for("api_v2.retrieve_article", article_id=a.id))


@blueprint.route("/articles/<article_id>", methods=["GET"])
@api_key_optional
@swag(swag_summary='Retrieve an article', swag_spec=ArticlesCrudApi.retrieve_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('retrieve_article', 'Retrieve article'), record_value_of_which_arg='article_id')
def retrieve_article(article_id):
    a = ArticlesCrudApi.retrieve(article_id, current_user)
    return jsonify_models(a)


@blueprint.route("/articles/<article_id>", methods=["PUT"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Update an article <span class="red">[Authenticated, not public]</span>', swag_spec=ArticlesCrudApi.update_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('update_article', 'Update article'), record_value_of_which_arg='article_id')
def update_article(article_id):
    # get the data from the request
    try:
        data = json.loads(request.data.decode("utf-8"))
    except:
        raise Api400Error("Supplied data was not valid JSON")

    # delegate to the API implementation
    ArticlesCrudApi.update(article_id, data, current_user)

    # respond with a suitable No Content successful response
    return no_content()


@blueprint.route("/articles/<article_id>", methods=["DELETE"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Delete an article <span class="red">[Authenticated, not public]</span>', swag_spec=ArticlesCrudApi.delete_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('delete_article', 'Delete article'), record_value_of_which_arg='article_id')
def delete_article(article_id):
    ArticlesCrudApi.delete(article_id, current_user)
    return no_content()


#########################################
# Journal R API

@blueprint.route('/journals/<journal_id>', methods=['GET'])
@api_key_optional
@swag(swag_summary='Retrieve a journal by ID', swag_spec=JournalsCrudApi.retrieve_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('retrieve_journal', 'Retrieve journal'), record_value_of_which_arg='journal_id')
def retrieve_journal(journal_id):
    return jsonify_data_object(JournalsCrudApi.retrieve(journal_id, current_user))


#########################################
# Application Bulk API

@blueprint.route("/bulk/applications", methods=["POST"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Create applications in bulk <span class="red">[Authenticated, not public]</span>', swag_spec=ApplicationsBulkApi.create_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('bulk_application_create', 'Bulk application create'))
def bulk_application_create():
    # get the data from the request
    try:
        data = json.loads(request.data.decode("utf-8"))
    except:
        raise Api400Error("Supplied data was not valid JSON")

    # delegate to the API implementation
    ids = ApplicationsBulkApi.create(data, current_user._get_current_object())

    # get all the locations for the ids
    inl = []
    for id in ids:
        inl.append((id, url_for("api_v2.retrieve_application", application_id=id)))

    # respond with a suitable Created response
    return bulk_created(inl)


@blueprint.route("/bulk/applications", methods=["DELETE"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Delete applications in bulk <span class="red">[Authenticated, not public]</span>', swag_spec=ApplicationsBulkApi.delete_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('bulk_application_delete', 'Bulk application delete'))
def bulk_application_delete():
    # get the data from the request
    try:
        data = json.loads(request.data.decode("utf-8"))
    except:
        raise Api400Error("Supplied data was not valid JSON")

    ApplicationsBulkApi.delete(data, current_user._get_current_object())

    return no_content()


#########################################
# Article Bulk API

@blueprint.route("/bulk/articles", methods=["POST"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Bulk article creation <span class="red">[Authenticated, not public]</span>', swag_spec=ArticlesBulkApi.create_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('bulk_article_create', 'Bulk article create'))
def bulk_article_create():
    # get the data from the request
    try:
        data = json.loads(request.data.decode("utf-8"))
    except:
        raise Api400Error("Supplied data was not valid JSON")

    # delegate to the API implementation
    ids = ArticlesBulkApi.create(data, current_user._get_current_object())

    # get all the locations for the ids
    inl = []
    for id in ids:
        inl.append((id, url_for("api_v2.retrieve_article", article_id=id)))

    # respond with a suitable Created response
    return bulk_created(inl)


@blueprint.route("/bulk/articles", methods=["DELETE"])
@api_key_required
@write_required(api=True)
@swag(swag_summary='Bulk article delete <span class="red">[Authenticated, not public]</span>', swag_spec=ArticlesBulkApi.delete_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('bulk_article_delete', 'Bulk article delete'))
def bulk_article_delete():
    # get the data from the request
    try:
        data = json.loads(request.data.decode("utf-8"))
    except:
        raise Api400Error("Supplied data was not valid JSON")

    ArticlesBulkApi.delete(data, current_user._get_current_object())

    return no_content()
