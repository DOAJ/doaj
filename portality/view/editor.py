from flask import Blueprint, request, flash, abort
from flask import render_template, redirect, url_for
from flask_login import current_user, login_required

from portality.core import app
from portality.decorators import ssl_required, restrict_to_role, write_required
from portality import models
from portality.bll import DOAJ, exceptions
from portality.lcc import lcc_jstree

from portality import lock
from portality.forms.application_forms import ApplicationFormFactory, JournalFormFactory
from portality import constants
from portality.crosswalks.application_form import ApplicationFormXWalk

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
    auth_svc = DOAJ.authorisationService()
    journal_svc = DOAJ.journalService()

    journal, _ = journal_svc.journal(journal_id)
    if journal is None:
        abort(404)

    try:
        auth_svc.can_edit_journal(current_user._get_current_object(), journal)
    except exceptions.AuthoriseException:
        abort(401)

    # # now check whether the user is the editor of the editor group
    role = "associate_editor"
    eg = models.EditorGroup.pull_by_key("name", journal.editor_group)
    if eg is not None and eg.editor == current_user.id:
        role = "editor"

    # attempt to get a lock on the object
    try:
        lockinfo = lock.lock(constants.LOCK_JOURNAL, journal_id, current_user.id)
    except lock.Locked as l:
        return render_template("editor/journal_locked.html", journal=journal, lock=l.lock, lcc_tree=lcc_jstree)

    fc = JournalFormFactory.context(role)

    if request.method == "GET":
        fc.processor(source=journal)
        return fc.render_template(lock=lockinfo, obj=journal, lcc_tree=lcc_jstree)

    elif request.method == "POST":
        processor = fc.processor(formdata=request.form, source=journal)
        if processor.validate(current_user):
            try:
                processor.finalise()
                flash('Journal updated.', 'success')
                for a in processor.alert:
                    flash_with_url(a, "success")
                return redirect(url_for("editor.journal_page", journal_id=journal.id, _anchor='done'))
            except Exception as e:
                flash(str(e))
                return redirect(url_for("editor.journal_page", journal_id=journal.id, _anchor='cannot_edit'))
        else:
            return fc.render_template(lock=lockinfo, obj=journal, lcc_tree=lcc_jstree)


@blueprint.route("/application/<application_id>", methods=["GET", "POST"])
@write_required()
@login_required
@ssl_required
def application(application_id):
    ap = models.Application.pull(application_id)

    if ap is None:
        abort(404)

    auth_svc = DOAJ.authorisationService()
    try:
        auth_svc.can_edit_application(current_user._get_current_object(), ap)
    except exceptions.AuthoriseException:
        abort(401)

    try:
        lockinfo = lock.lock(constants.LOCK_APPLICATION, application_id, current_user.id)
    except lock.Locked as l:
        return render_template("editor/suggestion_locked.html", suggestion=ap, lock=l.lock, edit_suggestion_page=True)

    form_diff, current_journal = ApplicationFormXWalk.update_request_diff(ap)

    # Edit role is either associate_editor or editor, depending whether the user is group leader
    eg = models.EditorGroup.pull_by_key("name", ap.editor_group)
    role = 'editor' if eg is not None and eg.editor == current_user.id else 'associate_editor'
    fc = ApplicationFormFactory.context(role)

    if request.method == "GET":
        fc.processor(source=ap)
        return fc.render_template(obj=ap, lock=lockinfo, form_diff=form_diff, current_journal=current_journal,
                                  lcc_tree=lcc_jstree)

    elif request.method == "POST":
        processor = fc.processor(formdata=request.form, source=ap)
        if processor.validate():
            try:
                processor.finalise(current_user)
                flash('Application updated.', 'success')
                for a in processor.alert:
                    flash_with_url(a, "success")
                return redirect(url_for("editor.application", application_id=ap.id, _anchor='done'))
            except Exception as e:
                flash(str(e))
                return fc.render_template(obj=ap, lock=lockinfo, form_diff=form_diff, current_journal=current_journal,
                                  lcc_tree=lcc_jstree)
        else:
            return fc.render_template(obj=ap, lock=lockinfo, form_diff=form_diff, current_journal=current_journal,
                                  lcc_tree=lcc_jstree)
