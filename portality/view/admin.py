import json

from flask import Blueprint, request, flash, abort, make_response
from flask import render_template, redirect, url_for
from flask.ext.login import current_user, login_required

from portality.core import app
import portality.models as models
import portality.util as util


blueprint = Blueprint('admin', __name__)

# restrict everything in admin to logged in users with the "admin" role
@blueprint.before_request
def restrict():
    if current_user.is_anonymous() or not current_user.has_role("admin"):
        abort(401)    
    

# build an admin page where things can be done
@blueprint.route('/')
@login_required
def index():
    return render_template('admin/index.html')

@blueprint.route("/journals")
@login_required
def journals():
    return render_template('admin/journals.html',
               search_page=True,
               facetviews=['journals']
           )

@blueprint.route("/journal/<journal_id>", methods=["GET", "POST"])
@login_required
def journal_page(journal_id):
    if not current_user.has_role("edit_journal"):
        abort(401)
    j = models.Journal.pull(journal_id)
    if j is None:
        abort(404)
        
    if request.method == "GET":
        return render_template("admin/journal.html", journal=j)

    elif request.method == "POST":
        #req = json.loads(request.data)
        #new_status = req.get("status")
        #s.set_application_status(new_status)
        #s.save()
        #return "", 204
        abort(501) # not implemented


@blueprint.route("/suggestions")
@login_required
def suggestions():
    return render_template('admin/suggestions.html',
               search_page=True,
               facetviews=['suggestions']
           )

@blueprint.route("/suggestion/<suggestion_id>", methods=["GET", "POST"])
@login_required
def suggestion_page(suggestion_id):
    if not current_user.has_role("edit_suggestion"):
        abort(401)
    s = models.Suggestion.pull(suggestion_id)
    if s is None:
        abort(404)
        
    if request.method == "GET":
        return render_template("admin/suggestion.html", suggestion=s)

    elif request.method == "POST":
        req = json.loads(request.data)
        new_status = req.get("status")
        s.set_application_status(new_status)
        s.save()
        return "", 204
