from flask import Blueprint, url_for, redirect, request

from portality.api.v1 import Api400Error
from portality.api.v1 import ApplicationsCrudApi, ArticlesCrudApi, JournalsCrudApi, ApplicationsBulkApi, ArticlesBulkApi
from portality.api.v1 import DiscoveryApi
from portality.core import app
from portality.decorators import api_key_required, api_key_optional, swag, write_required
from portality.lib import analytics

blueprint = Blueprint('api_v1', __name__)

API_VERSION_NUMBER = '1.0.0'

# Google Analytics category for API events
GA_CATEGORY = app.config.get('GA_CATEGORY_API', 'API Hit')
GA_ACTIONS = app.config.get('GA_ACTIONS_API', {})

API_V1_ERROR = "Version 1 is no longer supported."

# the API v1 is not supported anymore, this file handles api v1 requests:
# requests to articles are redirected to v2
# other requests raise the 400 Error

#######################################
# ARTICLES


@blueprint.route('/')
def api_v1_root():
    return redirect(url_for('.api_spec'))


@blueprint.route('/search/articles/<path:search_query>')
def search_articles(search_query):
    return redirect(url_for('api_v2.search_articles', search_query=search_query))


@blueprint.route("/articles", methods=["POST"])
@api_key_required
@write_required(api=True)
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('create_article', 'Create article'))
def create_article():
    print(request.args["api_key"])
    return redirect(url_for('api_v2.create_article', **request.args), code=307)


@blueprint.route("/articles/<article_id>", methods=["GET"])
@api_key_optional
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('retrieve_article', 'Retrieve article'),
                          record_value_of_which_arg='article_id')
def retrieve_article(article_id):
    return redirect(url_for('api_v2.retrieve_article', article_id=article_id))


@blueprint.route("/articles/<article_id>", methods=["PUT"])
@api_key_required
@write_required(api=True)
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('update_article', 'Update article'),
                          record_value_of_which_arg='article_id')
def update_article(article_id):
    return redirect(url_for('api_v2.search_articles', article_id=article_id, **request.args), code=307)


@blueprint.route("/articles/<article_id>", methods=["DELETE"])
@api_key_required
@write_required(api=True)
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('delete_article', 'Delete article'),
                          record_value_of_which_arg='article_id')
def delete_article(article_id):
    return redirect(url_for('api_v2.delete_article', article_id=article_id, **request.args), code=307)


@blueprint.route("/bulk/articles", methods=["POST"])
@api_key_required
@write_required(api=True)
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('bulk_article_create', 'Bulk article create'))
def bulk_article_create():
    return redirect(url_for('api_v2.bulk_article_create', **request.args), code=307)


@blueprint.route("/bulk/articles", methods=["DELETE"])
@api_key_required
@write_required(api=True)
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('bulk_article_delete', 'Bulk article delete'))
def bulk_article_delete():
    return redirect(url_for('api_v2.bulk_article_delete', **request.args), code=307)


#######################################
# OTHER

@blueprint.route('/journals/<journal_id>', methods=['GET'])
@api_key_optional
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('retrieve_journal', 'Retrieve journal'),
                          record_value_of_which_arg='journal_id')
def retrieve_journal(journal_id):
    raise Api400Error(API_V1_ERROR)


@blueprint.route("/bulk/applications", methods=["POST"])
@api_key_required
@write_required(api=True)
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('bulk_application_create', 'Bulk application create'))
def bulk_application_create():
    raise Api400Error(API_V1_ERROR)


@blueprint.route("/bulk/applications", methods=["DELETE"])
@api_key_required
@write_required(api=True)
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('bulk_application_delete', 'Bulk application delete'))
def bulk_application_delete():
    raise Api400Error(API_V1_ERROR)


@blueprint.route("/applications", methods=["POST"])
@api_key_required
@write_required(api=True)
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('create_application', 'Create application'))
def create_application():
    raise Api400Error(API_V1_ERROR)


@blueprint.route("/applications/<application_id>", methods=["GET"])
@api_key_required
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('retrieve_application', 'Retrieve application'),
                          record_value_of_which_arg='application_id')
def retrieve_application(application_id):
    raise Api400Error(API_V1_ERROR)


@blueprint.route("/applications/<application_id>", methods=["PUT"])
@api_key_required
@write_required(api=True)
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('update_application', 'Update application'),
                          record_value_of_which_arg='application_id')
def update_application(application_id):
    raise Api400Error(API_V1_ERROR)


@blueprint.route("/applications/<application_id>", methods=["DELETE"])
@api_key_required
@write_required(api=True)
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('delete_application', 'Delete application'),
                          record_value_of_which_arg='application_id')
def delete_application(application_id):
    raise Api400Error(API_V1_ERROR)


@blueprint.route("/search/applications/<path:search_query>")
@api_key_required
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('search_applications', 'Search applications'),
                          record_value_of_which_arg='search_query')
def search_applications(search_query):
    raise Api400Error(API_V1_ERROR)


@blueprint.route('/search/journals/<path:search_query>')
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('search_journals', 'Search journals'),
                          record_value_of_which_arg='search_query')
def search_journals(search_query):
    raise Api400Error(API_V1_ERROR)
