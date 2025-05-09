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
from portality.view.view_helper import exparam_editing_user
from portality.ui import templates

blueprint = Blueprint('editor', __name__)

# restrict everything in admin to logged in users with the "admin" role
@blueprint.before_request
def restrict():
    return restrict_to_role('editor_area')

@blueprint.route("/")
@login_required
@ssl_required
def index():
    # ~~-> Todo:Service~~
    svc = DOAJ.todoService()
    todos = svc.top_todo(current_user._get_current_object(), size=app.config.get("TODO_LIST_SIZE"), update_requests=False)
    count = svc.user_finished_historical_counts(current_user._get_current_object())
    # ~~-> Dashboard:Page~~
    return render_template(templates.EDITOR_DASHBOARD, todos=todos, historical_count=count)


@blueprint.route('/group_applications')
@login_required
@ssl_required
def group_suggestions():
    return render_template(templates.EDITOR_GROUP_APPLICATIONS_SEARCH)


@blueprint.route('/your_applications')
@login_required
@ssl_required
def associate_suggestions():
    return render_template(templates.EDITOR_YOUR_APPLICATIONS_SEARCH)

# Editors no longer manage journals, so this code is obsolete, but nonetheless
# it's useful to keep it around for reference

# @blueprint.route('/journal/<journal_id>', methods=["GET", "POST"])
# @login_required
# @ssl_required
# @write_required()
# def journal_page(journal_id):
#     auth_svc = DOAJ.authorisationService()
#     journal_svc = DOAJ.journalService()
#
#     journal, _ = journal_svc.journal(journal_id)
#     if journal is None:
#         abort(404)
#
#     try:
#         auth_svc.can_edit_journal(current_user._get_current_object(), journal)
#     except exceptions.AuthoriseException:
#         abort(401)
#
#     # # now check whether the user is the editor of the editor group
#     role = "associate_editor"
#     eg = models.EditorGroup.pull_by_key("name", journal.editor_group)
#     if eg is not None and eg.editor == current_user.id:
#         role = "editor"
#
#     # attempt to get a lock on the object
#     try:
#         lockinfo = lock.lock(constants.LOCK_JOURNAL, journal_id, current_user.id)
#     except lock.Locked as l:
#         return render_template("editor/journal_locked.html", journal=journal, lock=l.lock, lcc_tree=lcc_jstree)
#
#     fc = JournalFormFactory.context(role, extra_param=exparam_editing_user())
#
#     if request.method == "GET":
#         fc.processor(source=journal)
#         return fc.render_template(lock=lockinfo, obj=journal, lcc_tree=lcc_jstree)
#
#     elif request.method == "POST":
#         processor = fc.processor(formdata=request.form, source=journal)
#         if processor.validate():
#             try:
#                 processor.finalise()
#                 flash('Journal updated.', 'success')
#                 for a in processor.alert:
#                     flash_with_url(a, "success")
#                 return redirect(url_for("editor.journal_page", journal_id=journal.id, _anchor='done'))
#             except Exception as e:
#                 flash(str(e))
#                 return redirect(url_for("editor.journal_page", journal_id=journal.id, _anchor='cannot_edit'))
#         else:
#             return fc.render_template(lock=lockinfo, obj=journal, lcc_tree=lcc_jstree)

@blueprint.route("/journal/readonly/<journal_id>", methods=["GET"])
@login_required
@ssl_required
def journal_readonly(journal_id):
    j = models.Journal.pull(journal_id)
    if j is None:
        abort(404)

    fc = JournalFormFactory.context("editor_readonly")
    fc.processor(source=j)
    return fc.render_template(obj=j, lcc_tree=lcc_jstree, notabs=True)


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
        return render_template(templates.EDITOR_APPLICATION_LOCKED, application=ap, lock=l.lock)

    form_diff, current_journal = ApplicationFormXWalk.update_request_diff(ap)

    # Edit role is either associate_editor or editor, depending whether the user is group leader
    eg = models.EditorGroup.pull_by_key("name", ap.editor_group)
    role = 'editor' if eg is not None and eg.editor == current_user.id else 'associate_editor'
    fc = ApplicationFormFactory.context(role, extra_param=exparam_editing_user())

    if request.method == "GET":
        fc.processor(source=ap)
        return fc.render_template(obj=ap, lock=lockinfo, form_diff=form_diff, current_journal=current_journal,
                                  lcc_tree=lcc_jstree)

    elif request.method == "POST":
        processor = fc.processor(formdata=request.form, source=ap)
        if processor.validate():
            try:
                processor.finalise()
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
