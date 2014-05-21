from flask import Blueprint, request, flash, abort, make_response
from flask import render_template, redirect, url_for
from flask.ext.login import current_user, login_required

from portality.core import app, ssl_required, restrict_to_role
from portality import models

from portality import journal as journal_handler

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

@blueprint.route('/your_journals')
@login_required
@ssl_required
def associate_journals():
    return render_template("editor/associate_journals.html", search_page=True, facetviews=["associate_journals"])

@blueprint.route('/your_applications')
@login_required
@ssl_required
def associate_suggestions():
    pass

@blueprint.route('/journal/<journal_id>', methods=["GET", "POST"])
@login_required
@ssl_required
def journal_page(journal_id):
    # user must have the role "edit_journal"
    if not current_user.has_role("edit_journal"):
        abort(401)

    # get the journal, so we can check our permissions against it
    j = journal_handler.get_journal(journal_id)

    # flag which we can set to determine whether this user can access the editorial
    # features of the journal form
    editorial_available = False

    # user must be either the "admin.editor" of the journal, or the editor of the "admin.editor_group"

    # is the user the currently assigned editor of the journal?
    passed = False
    if j.editor == current_user.id:
        passed = True

    # now check whether the user is the editor of the editor group
    # and simultaneously determine whether they have editorial rights
    # on this journal
    eg = models.EditorGroup.pull_by_key("name", j.editor_group)
    if eg is not None and eg.editor == current_user.id:
        passed = True
        editorial_available = True

    # if the user wasn't the editor or the owner of the editor group, unauthorised
    if not passed:
        abort(401)

    # create the list of allowable editors for this journal (the editor
    # and all the associates in this editor group)
    # egs = models.EditorGroup.groups_by_editor(current_user.id)
    editors = [current_user.id]
    editors += eg.associates
    editors = list(set(editors))

    return journal_handler.request_handler(request, journal_id, redirect_route="editor.journal_page",
                                           template="editor/journal.html", editors=editors,
                                           editorial_available=editorial_available)