from flask import Blueprint, request, flash, abort
from flask import render_template, redirect, url_for
from flask_login import current_user, login_required

from portality.core import app
from portality.decorators import ssl_required, restrict_to_role, write_required
from portality import models

from portality import lock
from portality.formcontext import formcontext
from portality.util import flash_with_url

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
    return render_template('editor/index.html', editor_of=editor_of, associate_of=associate_of, managing_editor=app.config.get("MANAGING_EDITOR_EMAIL"))

@blueprint.route('/group_journals')
@login_required
@ssl_required
def group_journals():
    return render_template("editor/group_journals.html")

@blueprint.route('/group_applications')
@login_required
@ssl_required
def group_suggestions():
    return render_template("editor/group_applications.html")

@blueprint.route('/your_journals')
@login_required
@ssl_required
def associate_journals():
    return render_template("editor/associate_journals.html")

@blueprint.route('/your_applications')
@login_required
@ssl_required
def associate_suggestions():
    return render_template("editor/associate_applications.html")

@blueprint.route('/journal/<journal_id>', methods=["GET", "POST"])
@login_required
@ssl_required
@write_required()
def journal_page(journal_id):
    # user must have the role "edit_journal"
    if not current_user.has_role("edit_journal"):
        abort(401)

    # get the journal, so we can check our permissions against it
    j = models.Journal.pull(journal_id)
    if j is None:
        abort(404)

    # user must be either the "admin.editor" of the journal, or the editor of the "admin.editor_group"

    # is the user the currently assigned editor of the journal?
    passed = False
    if j.editor == current_user.id:
        passed = True

    # now check whether the user is the editor of the editor group
    role = "associate_editor"
    eg = models.EditorGroup.pull_by_key("name", j.editor_group)
    if eg is not None and eg.editor == current_user.id:
        passed = True
        role = "editor"

    # if the user wasn't the editor or the owner of the editor group, unauthorised
    if not passed:
        abort(401)

    # attempt to get a lock on the object
    try:
        lockinfo = lock.lock("journal", journal_id, current_user.id)
    except lock.Locked as l:
        return render_template("editor/journal_locked.html", journal=j, lock=l.lock, edit_journal_page=True)

    if request.method == "GET":
        fc = formcontext.JournalFormFactory.get_form_context(role=role, source=j)
        return fc.render_template(edit_journal_page=True, lock=lockinfo)
    elif request.method == "POST":
        fc = formcontext.JournalFormFactory.get_form_context(role=role, form_data=request.form, source=j)
        if fc.validate():
            try:
                fc.finalise()
                flash('Journal updated.', 'success')
                for a in fc.alert:
                    flash_with_url(a, "success")
                return redirect(url_for("editor.journal_page", journal_id=j.id, _anchor='done'))
            except formcontext.FormContextException as e:
                flash(str(e))
                return redirect(url_for("editor.journal_page", journal_id=j.id, _anchor='cannot_edit'))
        else:
            return fc.render_template(edit_journal_page=True, lock=lockinfo)


@blueprint.route('/suggestion/<suggestion_id>', methods=["GET", "POST"])
@login_required
@ssl_required
@write_required()
def suggestion_page(suggestion_id):
    # user must have the role "edit_journal"
    if not current_user.has_role("edit_suggestion"):
        abort(401)

    # get the suggestion, so we can check our permissions against it
    s = models.Suggestion.pull(suggestion_id)
    if s is None:
        abort(404)

    # user must be either the "admin.editor" of the suggestion, or the editor of the "admin.editor_group"

    # is the user the currently assigned editor of the suggestion?
    passed = False
    if s.editor == current_user.id:
        passed = True

    # now check whether the user is the editor of the editor group
    role = "associate_editor"
    eg = models.EditorGroup.pull_by_key("name", s.editor_group)
    if eg is not None and eg.editor == current_user.id:
        passed = True
        role = "editor"

    # if the user wasn't the editor or the owner of the editor group, unauthorised
    if not passed:
        abort(401)

    # attempt to get a lock on the object
    try:
        lockinfo = lock.lock("suggestion", suggestion_id, current_user.id)
    except lock.Locked as l:
        return render_template("editor/suggestion_locked.html", suggestion=s, lock=l.lock, edit_suggestion_page=True)

    if request.method == "GET":
        fc = formcontext.ApplicationFormFactory.get_form_context(role=role, source=s)
        return fc.render_template(edit_suggestion_page=True, lock=lockinfo)
    elif request.method == "POST":
        fc = formcontext.ApplicationFormFactory.get_form_context(role=role, form_data=request.form, source=s)
        if fc.validate():
            try:
                fc.finalise()
                flash('Application updated.', 'success')
                for a in fc.alert:
                    flash_with_url(a, "success")
                return redirect(url_for("editor.suggestion_page", suggestion_id=s.id, _anchor='done'))
            except formcontext.FormContextException as e:
                flash(e.message)
                return redirect(url_for("editor.suggestion_page", suggestion_id=s.id, _anchor='cannot_edit'))
        else:
            return fc.render_template(edit_suggestion_page=True, lock=lockinfo)
