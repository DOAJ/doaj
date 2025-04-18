import json
from io import BytesIO

from flask import Blueprint, make_response, abort, render_template, send_file
from flask_login import current_user, login_required

from portality import lock, models
from portality.bll import DOAJ
from portality.crosswalks.article_ris import ArticleRisXWalk
from portality.core import app
from portality.decorators import ssl_required, write_required
from portality.lib import plausible
from portality.util import jsonp
from portality.ui import templates

blueprint = Blueprint('doajservices', __name__)


@blueprint.route("/unlock/<object_type>/<object_id>", methods=["POST"])
@login_required
@ssl_required
@write_required()
def unlock(object_type, object_id):
    # change from suggestion to application after redesign, that needs refactoring to make the code consistent
    # that if is only for quick hotfix to make sure the functionality works
    if object_type == "application":
        object_type = "suggestion"

    # first figure out if we are allowed to even contemplate this action
    if object_type not in ["journal", "suggestion"]:
        abort(404)
    if object_type == "journal":
        if not current_user.has_role("edit_journal"):
            abort(401)
    if object_type == "suggestion":
        if not current_user.has_role("edit_suggestion"):
            abort(401)

    # try to unlock
    unlocked = lock.unlock(object_type, object_id, current_user.id)

    # if we couldn't unlock, this is a bad request
    if not unlocked:
        abort(400)

    # otherwise, return success
    resp = make_response(json.dumps({"result": "success"}))
    resp.mimetype = "application/json"
    return resp


@blueprint.route("/unlocked")
@login_required
def unlocked():
    """
    Redirect to this route on completion of an unlock
    :return:
    """
    if current_user.is_super:
        return render_template(templates.ADMIN_UNLOCKED)
    else:
        return render_template(templates.EDITOR_UNLOCKED)


# @blueprint.route("/shorten", methods=["POST"])
# @jsonp
# def shorten():
#     # Enable this if you are testing and you want to see the front end work, without working bit.ly credentials
#     # return make_response(json.dumps({"url" : "testing url"}))
#     try:
#         # parse the json
#         d = json.loads(request.data)
#         p = d['page']
#         q = d['query']
#
#         # re-serialise the query, and url encode it
#         source = urllib.parse.quote(json.dumps(q))
#
#         # assemble the DOAJ url
#         doajurl = p + "?source=" + source
#
#         # assemble the bitly url.  Note that we re-encode the doajurl to include in the
#         # query arguments, so by this point it is double-encoded
#         bitly = app.config.get("BITLY_SHORTENING_API_URL")
#         bitly_oauth = app.config.get("BITLY_OAUTH_TOKEN")
#
#         # Set an Auth Bearer token (Bitly 4.0)
#         headers = {'Authorization': 'Bearer ' + bitly_oauth}
#
#         # Add the long url as a payload
#         payload = {'long_url': doajurl}
#
#         # make the request
#         resp = requests.post(bitly, headers=headers, data=json.dumps(payload))
#         shorturl = resp.json().get('link')
#
#         if not shorturl:
#             abort(400)
#
#         # make the response
#         answer = make_response(json.dumps({"url": shorturl}))
#         answer.mimetype = "application/json"
#         return answer
#     except:
#         abort(400)


@blueprint.route("/groupstatus/<group_id>", methods=["GET"])
@jsonp
@login_required
def group_status(group_id):
    """
    ~~GroupStatus:Feature -> Todo:Service~~
    :param group_id:
    :return:
    """
    if (not (current_user.has_role("editor") and models.EditorGroup.pull(group_id).editor == current_user.id)) and (
            not current_user.has_role("admin")):
        abort(404)
    svc = DOAJ.todoService()
    stats = svc.group_stats(group_id)
    return make_response(json.dumps(stats))


@blueprint.route("/autocheck/dismiss/<autocheck_set_id>/<autocheck_id>", methods=["GET", "POST"])
@jsonp
@login_required
def dismiss_autocheck(autocheck_set_id, autocheck_id):
    if not current_user.has_role("admin"):
        abort(404)
    svc = DOAJ.autochecksService()
    done = svc.dismiss(autocheck_set_id, autocheck_id)
    if not done:
        abort(404)
    return make_response(json.dumps({"status": "success"}))


@blueprint.route("/autocheck/undismiss/<autocheck_set_id>/<autocheck_id>", methods=["GET", "POST"])
@jsonp
@login_required
def undismiss_autocheck(autocheck_set_id, autocheck_id):
    if not current_user.has_role("admin"):
        abort(404)
    svc = DOAJ.autochecksService()
    done = svc.undismiss(autocheck_set_id, autocheck_id)
    if not done:
        abort(404)
    return make_response(json.dumps({"status": "success"}))


@blueprint.route('/export/article/<article_id>/<fmt>')
@plausible.pa_event(app.config.get('ANALYTICS_CATEGORY_RIS', 'RIS'),
                    action=app.config.get('ANALYTICS_ACTION_RISEXPORT', 'Export'), record_value_of_which_arg='article_id')
def export_article_ris(article_id, fmt):
    article = models.Article.pull(article_id)
    if not article:
        abort(404)

    if fmt != 'ris':
        # only support ris for now
        abort(404)

    byte_stream = BytesIO()
    ris = ArticleRisXWalk.article2ris(article)
    byte_stream.write(ris.to_text().encode('utf-8', errors='ignore'))
    byte_stream.seek(0)

    filename = f'article-{article_id[:10]}.ris'

    resp = make_response(send_file(byte_stream, as_attachment=True, download_name=filename))
    return resp
