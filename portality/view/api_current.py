from flask import Blueprint

from portality.view import api_v3, api_v4

LATEST_API_VERSION_NUMBER = api_v4.API_VERSION_NUMBER

blueprint = Blueprint('api_current', __name__)

# url and api version binding
blueprint.route('/')(api_v3.api_root)
blueprint.route('/swagger.json')(api_v4.api_spec)
blueprint.route('/docs')(api_v4.docs)
(blueprint.route
 ("/<path:invalid_path>", methods=["POST", "GET", "PUT", "DELETE", "PATCH", "HEAD"])
 (api_v3.missing_resource)
 )
blueprint.route("/search/applications/<path:search_query>")(api_v3.search_applications)
blueprint.route('/search/journals/<path:search_query>')(api_v3.search_journals)
blueprint.route('/search/articles/<path:search_query>')(api_v3.search_articles)
blueprint.route("/applications", methods=["POST"])(api_v3.create_application)
blueprint.route("/applications/<application_id>", methods=["GET"])(api_v3.retrieve_application)
blueprint.route("/applications/<application_id>", methods=["PUT"])(api_v3.update_application)
blueprint.route("/applications/<application_id>", methods=["DELETE"])(api_v3.delete_application)
blueprint.route("/articles", methods=["POST"])(api_v3.create_article)
blueprint.route("/articles/<article_id>", methods=["GET"])(api_v3.retrieve_article)
blueprint.route("/articles/<article_id>", methods=["PUT"])(api_v3.update_article)
blueprint.route("/articles/<article_id>", methods=["DELETE"])(api_v3.delete_article)
blueprint.route('/journals/<journal_id>', methods=['GET'])(api_v3.retrieve_journal)
blueprint.route("/bulk/applications", methods=["POST"])(api_v3.bulk_application_create)
blueprint.route("/bulk/applications", methods=["DELETE"])(api_v3.delete_application)
blueprint.route("/bulk/articles", methods=["POST"])(api_v4.bulk_article_create)
blueprint.route("/bulk/articles", methods=["DELETE"])(api_v3.bulk_article_delete)
