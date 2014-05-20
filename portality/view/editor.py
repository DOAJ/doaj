import json
from datetime import datetime

from flask import Blueprint, request, flash, abort, make_response
from flask import render_template, redirect, url_for
from flask.ext.login import current_user, login_required

from portality.core import app, ssl_required, restrict_to_role
from portality import models

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
    editor_of = models.EditorGroup.groups_by_editor(current_user.id)
    associate_of = models.EditorGroup.groups_by_associate(current_user.id)
    return render_template('editor/index.html', editor_of=editor_of, associate_of=associate_of)

@blueprint.route('/group_journals')
@login_required
@ssl_required
def group_journals():
    return render_template("editor/group_journals.html", search_page=True, facetviews=["group_journals"])

@blueprint.route('/group_applications')
@login_required
@ssl_required
def group_suggestions():
    pass

@blueprint.route('/journal/<journal_id>', methods=["GET", "POST"])
@login_required
@ssl_required
def journal_page(journal_id):
    return render_template("editor/group_journals.html", search_page=True, facetviews=["group_journals"])