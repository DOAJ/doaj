import json
from datetime import datetime

from flask import Blueprint, request, flash, abort, make_response
from flask import render_template, redirect, url_for
from flask.ext.login import current_user, login_required

from portality.core import app, ssl_required, restrict_to_role

blueprint = Blueprint('editor', __name__)

# restrict everything in admin to logged in users with the "admin" role
@blueprint.before_request
def restrict():
    return restrict_to_role('editor_area')

# build an editor's page where things can be done
@blueprint.route('/')
@login_required
@ssl_required
def index():
    return render_template('editor/index.html')