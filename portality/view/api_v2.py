from flask import Blueprint, url_for, redirect, request

from portality.api.current import Api400Error
from portality.view import api_v3
from portality.core import app
from portality.decorators import api_key_required, api_key_optional, swag, write_required
from portality.lib import analytics

blueprint = Blueprint('api_v2', __name__)

API_VERSION_NUMBER = '2.0.0'

# Google Analytics category for API events
GA_CATEGORY = app.config.get('GA_CATEGORY_API', 'API Hit')
GA_ACTIONS = app.config.get('GA_ACTIONS_API', {})

API_UNSUPPORTED_ERROR = "Version 2 is no longer supported."

# the API v2 is not supported anymore, this file handles api v3 requests:
# requests to articles are redirected to v3
# other requests raise the 400 Error

#######################################
# ARTICLES


@blueprint.route('/')
def api_v2_root():
    return redirect(url_for('api_v3.api_spec'))


@blueprint.route('/docs')
def docs():
    return redirect(url_for('doaj.docs'))


@blueprint.route('/search/articles/<path:search_query>')
def search_articles(search_query):
    # Redirects are disabled https://github.com/DOAJ/doajPM/issues/2664
    # return redirect(url_for('api_v3.search_articles', search_query=search_query))
    return api_v3.search_articles(search_query)


@blueprint.route("/articles", methods=["POST"])
@api_key_required
@write_required(api=True)
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('create_article', 'Create article'))
def create_article():
    # Redirects are disabled https://github.com/DOAJ/doajPM/issues/2664
    # return redirect(url_for('api_v3.create_article', **request.args), code=301)
    return api_v3.create_article()


@blueprint.route("/articles/<article_id>", methods=["GET"])
@api_key_optional
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('retrieve_article', 'Retrieve article'),
                          record_value_of_which_arg='article_id')
def retrieve_article(article_id):
    # Redirects are disabled https://github.com/DOAJ/doajPM/issues/2664
    # return redirect(url_for('api_v3.retrieve_article', article_id=article_id, **request.args), code=301)
    return api_v3.retrieve_article(article_id)


@blueprint.route("/articles/<article_id>", methods=["PUT"])
@api_key_required
@write_required(api=True)
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('update_article', 'Update article'),
                          record_value_of_which_arg='article_id')
def update_article(article_id):
    # Redirects are disabled https://github.com/DOAJ/doajPM/issues/2664
    # return redirect(url_for('api_v3.update_article', article_id=article_id, **request.args), code=301)
    return api_v3.update_article(article_id)


@blueprint.route("/articles/<article_id>", methods=["DELETE"])
@api_key_required
@write_required(api=True)
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('delete_article', 'Delete article'),
                          record_value_of_which_arg='article_id')
def delete_article(article_id):
    # Redirects are disabled https://github.com/DOAJ/doajPM/issues/2664
    # return redirect(url_for('api_v3.delete_article', article_id=article_id, **request.args), code=301)
    return api_v3.delete_article(article_id)


@blueprint.route("/bulk/articles", methods=["POST"])
@api_key_required
@write_required(api=True)
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('bulk_article_create', 'Bulk article create'))
def bulk_article_create():
    # Redirects are disabled https://github.com/DOAJ/doajPM/issues/2664
    # return redirect(url_for('api_v3.bulk_article_create', **request.args), code=301)
    return api_v3.bulk_article_create()


@blueprint.route("/bulk/articles", methods=["DELETE"])
@api_key_required
@write_required(api=True)
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('bulk_article_delete', 'Bulk article delete'))
def bulk_article_delete():
    # Redirects are disabled https://github.com/DOAJ/doajPM/issues/2664
    # return redirect(url_for('api_v3.bulk_article_delete', **request.args), code=301)
    return api_v3.bulk_article_delete()


#######################################
# OTHER

@blueprint.route('/journals/<journal_id>', methods=['GET'])
@api_key_optional
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('retrieve_journal', 'Retrieve journal'),
                          record_value_of_which_arg='journal_id')
def retrieve_journal(journal_id):
    # Redirects are disabled https://github.com/DOAJ/doajPM/issues/2664
    # return redirect(url_for('api_v3.retrieve_journal', journal_id=journal_id))
    return api_v3.retrieve_journal(journal_id)


@blueprint.route("/bulk/applications", methods=["POST"])
@api_key_required
@write_required(api=True)
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('bulk_application_create', 'Bulk application create'))
def bulk_application_create():
    raise Api400Error(API_UNSUPPORTED_ERROR)


@blueprint.route("/bulk/applications", methods=["DELETE"])
@api_key_required
@write_required(api=True)
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('bulk_application_delete', 'Bulk application delete'))
def bulk_application_delete():
    raise Api400Error(API_UNSUPPORTED_ERROR)


@blueprint.route("/applications", methods=["POST"])
@api_key_required
@write_required(api=True)
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('create_application', 'Create application'))
def create_application():
    raise Api400Error(API_UNSUPPORTED_ERROR)


@blueprint.route("/applications/<application_id>", methods=["GET"])
@api_key_required
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('retrieve_application', 'Retrieve application'),
                          record_value_of_which_arg='application_id')
def retrieve_application(application_id):
    raise Api400Error(API_UNSUPPORTED_ERROR)


@blueprint.route("/applications/<application_id>", methods=["PUT"])
@api_key_required
@write_required(api=True)
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('update_application', 'Update application'),
                          record_value_of_which_arg='application_id')
def update_application(application_id):
    raise Api400Error(API_UNSUPPORTED_ERROR)


@blueprint.route("/applications/<application_id>", methods=["DELETE"])
@api_key_required
@write_required(api=True)
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('delete_application', 'Delete application'),
                          record_value_of_which_arg='application_id')
def delete_application(application_id):
    raise Api400Error(API_UNSUPPORTED_ERROR)


@blueprint.route("/search/applications/<path:search_query>")
@api_key_required
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('search_applications', 'Search applications'),
                          record_value_of_which_arg='search_query')
def search_applications(search_query):
    # Redirects are disabled https://github.com/DOAJ/doajPM/issues/2664
    # return redirect(url_for('api_v3.search_applications', search_query=search_query))
    return api_v3.search_applications(search_query)


@blueprint.route('/search/journals/<path:search_query>')
@analytics.sends_ga_event(GA_CATEGORY, GA_ACTIONS.get('search_journals', 'Search journals'),
                          record_value_of_which_arg='search_query')
def search_journals(search_query):
    # Redirects are disabled https://github.com/DOAJ/doajPM/issues/2664
    # return redirect(url_for('api_v3.search_journals', search_query=search_query))
    return api_v3.search_journals(search_query)
