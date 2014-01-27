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

@blueprint.route("/suggestion/<suggestion_id>")
@login_required
def suggestion_page(suggestion_id):
    if not current_user.has_role("edit_suggestion"):
        abort(401)
    return render_template("admin/suggestion.html")

