from flask import Blueprint, jsonify, url_for, request, make_response, abort, render_template, redirect
from flask.ext.login import current_user

from flask_swagger import swagger

from portality.api.v1 import DiscoveryApi, DiscoveryException
from portality.api.v1 import ApplicationsCrudApi, ArticlesCrudApi, JournalsCrudApi
from portality.api.v1 import jsonify_models, jsonify_data_object, Api400Error, Api401Error, Api404Error, created, no_content
from portality.core import app
from portality.decorators import api_key_required, api_key_optional, swag

import json

blueprint = Blueprint('api_v1', __name__)

API_VERSION_NUMBER = '1.0.0'

@blueprint.route('/')
def api_v1_root():
    return redirect(url_for('.api_spec'))

@blueprint.route('/swagger.json')
def api_spec():
    swag = swagger(app)
    swag['info']['title'] = "DOAJ API documentation"
    # TODO use a Jinja template for the description below, HTML works. Emails use jinja templates already.
    auth_info = """
<p>Note that some routes require authentication and are only available to publishers who submit data to DOAJ or other collaborators who integrate more closely with DOAJ. If you think you could benefit from integrating more closely with DOAJ by using these routes, please <a href="{contact_us_url}">contact us</a>. If you already have an account, please log in as usual and click on your username in the top right corner to manage API keys.</p>
"""
    if current_user.is_authenticated():
        auth_info = """
        <p>Note that some routes require authentication. You can generate an API key and view your key for later reference at {account_url}.</p>
        """.format(account_url = url_for('account.username', username=current_user.id, _external=True))

    swag['info']['description'] = """
<p>This page documents the first version of the DOAJ API, v.{api_version}</p>
<p>Base URL: <a href="{base_url}" target="_blank">{base_url}</a></p>
<h2 id="intro">Using this live documentation page</h2>
This page contains a list of all routes available via the DOAJ API. It also serves as a live demo page. You can fill in the parameters needed by the API and it will construct and send a request to the live API for you, letting you see all the details you might need for your integration. Please note that not all fields will be available on all records. Further information on advanced usage of the routes is available at the bottom below the route list.

<h2 id="intro_auth">Authenticated routes</h2>
{auth_info}
""".format(
        api_version=API_VERSION_NUMBER,
        base_url=url_for('.api_v1_root', _external=True),
        contact_us_url=url_for('doaj.contact'),
        auth_info=auth_info
    )
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
    return render_template('doaj/api_docs.html')


@swag(swag_summary='Search your applications <span class="red">[Authenticated, not public]</span>', swag_spec=DiscoveryApi.get_application_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@blueprint.route("/search/applications/<path:search_query>")
@api_key_required
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
        results = DiscoveryApi.search_applications(current_user, search_query, page, psize, sort)
    except DiscoveryException as e:
        raise Api400Error(e.message)

    return jsonify_models(results)


@swag(swag_summary='Search journals', swag_spec=DiscoveryApi.get_journal_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@blueprint.route('/search/journals/<path:search_query>')
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
        results = DiscoveryApi.search_journals(search_query, page, psize, sort)
    except DiscoveryException as e:
        raise Api400Error(e.message)

    return jsonify_models(results)


@swag(swag_summary='Search articles', swag_spec=DiscoveryApi.get_article_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
@blueprint.route('/search/articles/<path:search_query>')
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
        results = DiscoveryApi.search_articles(search_query, page, psize, sort)
    except DiscoveryException as e:
        raise Api400Error(e.message)

    return jsonify_models(results)


#########################################
## Application CRUD API

@blueprint.route("/applications", methods=["POST"])
@api_key_required
@swag(swag_summary='Create an application', swag_spec=ApplicationsCrudApi.create_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
def create_application():
    # get the data from the request
    try:
        data = json.loads(request.data)
    except:
        raise Api400Error("Supplied data was not valid JSON")

    # delegate to the API implementation
    a = ApplicationsCrudApi.create(data, current_user)

    # respond with a suitable Created response
    return created(a, url_for("api_v1.retrieve_application", aid=a.id))

@blueprint.route("/application/<aid>", methods=["GET"])
@api_key_required
@swag(swag_summary='Retrieve an application', swag_spec=ApplicationsCrudApi.create_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
def retrieve_application(aid):
    a = ApplicationsCrudApi.retrieve(aid, current_user)
    return jsonify_models(a)

@blueprint.route("/application/<aid>", methods=["PUT"])
@api_key_required
@swag(swag_summary='Update an application', swag_spec=ApplicationsCrudApi.update_swag())  # must be applied after @api_key_(
def update_application(aid):
    # get the data from the request
    try:
        data = json.loads(request.data)
    except:
        raise Api400Error("Supplied data was not valid JSON")

    # delegate to the API implementation
    ApplicationsCrudApi.update(aid, data, current_user)

    # respond with a suitable No Content successful response
    return no_content()

@blueprint.route("/application/<aid>", methods=["DELETE"])
@api_key_required
@swag(swag_summary='Delete an application', swag_spec=ApplicationsCrudApi.delete_swag())  # must be applied after @api_key_(
def delete_application(aid):
    ApplicationsCrudApi.delete(aid, current_user)
    return no_content()


#########################################
## Article CRUD API

@blueprint.route("/articles", methods=["POST"])
@api_key_required
def create_article():
    # get the data from the request
    try:
        data = json.loads(request.data)
    except:
        raise Api400Error("Supplied data was not valid JSON")

    # delegate to the API implementation
    a = ArticlesCrudApi.create(data, current_user)

    # respond with a suitable Created response
    return created(a, url_for("api_v1.retrieve_article", aid=a.id))


@blueprint.route("/articles/<aid>", methods=["GET"])
@api_key_required
def retrieve_article(aid):
    a = ArticlesCrudApi.retrieve(aid, current_user)
    return jsonify_models(a)


@blueprint.route("/articles/<aid>", methods=["PUT"])
@api_key_required
def update_article(aid):
    # get the data from the request
    try:
        data = json.loads(request.data)
    except:
        raise Api400Error("Supplied data was not valid JSON")

    # delegate to the API implementation
    ArticlesCrudApi.update(aid, data, current_user)

    # respond with a suitable No Content successful response
    return no_content()


@blueprint.route("/articles/<aid>", methods=["DELETE"])
@api_key_required
def delete_article(aid):
    ArticlesCrudApi.delete(aid, current_user)
    return no_content()

@blueprint.route('/journals/<journal_id>', methods=['GET'])
@api_key_optional
@swag(swag_summary='Retrieve a journal by ID', swag_spec=JournalsCrudApi.retrieve_swag())  # must be applied after @api_key_(optional|required) decorators. They don't preserve func attributes.
def retrieve_journal(journal_id):
    return jsonify_data_object(JournalsCrudApi.retrieve(journal_id, current_user))