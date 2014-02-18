from flask import Blueprint, request, abort, make_response, Response
from flask import render_template, abort, redirect, url_for, flash
from flask.ext.login import current_user, login_required

from portality.core import app
from portality import settings

blueprint = Blueprint('publisher', __name__)

# restrict everything in admin to logged in users with the "publsiher" role
@blueprint.before_request
def restrict():
    if current_user.is_anonymous() or not current_user.has_role("publisher"):
        abort(401)    

@blueprint.route("/")
@login_required
def index():
    return render_template("publisher/index.html", search_page=True, facetviews=["publisher"])
