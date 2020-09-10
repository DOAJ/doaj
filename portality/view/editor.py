from flask import Blueprint, request, flash, abort
from flask import render_template, redirect, url_for
from flask_login import current_user, login_required

from portality.core import app
from portality.decorators import ssl_required, restrict_to_role, write_required
from portality import models
from portality.bll import DOAJ, exceptions

from portality import lock
from portality.forms.application_forms import ApplicationFormFactory, JournalFormFactory
from portality import constants

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
    eg = models.EditorGroup.pull_by_key("name", j.editor_group)
    if eg is not None and eg.editor == current_user.id:
        role = "editor"

    # attempt to get a lock on the object
    try:
        lockinfo = lock.lock(constants.LOCK_JOURNAL, journal_id, current_user.id)
    except lock.Locked as l:
        return render_template("editor/journal_locked.html", journal=journal, lock=l.lock)

    fc = JournalFormFactory.context(role)

    if request.method == "GET":
        fc.processor(source=journal)
        # fc = formcontext.JournalFormFactory.get_form_context(role=role, source=j)
        return fc.render_template(lock=lockinfo, obj=journal)

    elif request.method == "POST":
        processor = fc.processor(formdata=request.form, source=journal)
        # fc = formcontext.JournalFormFactory.get_form_context(role=role, form_data=request.form, source=j)
        if processor.validate():
            try:
                processor.finalise()
                flash('Journal updated.', 'success')
                for a in fc.alert:
                    flash_with_url(a, "success")
                return redirect(url_for("editor.journal_page", journal_id=journal.id, _anchor='done'))
            except Exception as e:
                flash(str(e))
                return redirect(url_for("editor.journal_page", journal_id=journal.id, _anchor='cannot_edit'))
        else:
            return fc.render_template(lock=lockinfo, obj=journal)


@blueprint.route("/application/<application_id>", methods=["GET", "POST"])
@write_required()
@login_required
@ssl_required
def application(application_id):
    # todo: this looks very much like the admin review form admin.application: can we refactor to be the same endpoint?
    ap = models.Application.pull(application_id)

    if ap is None:
        abort(404)

    auth_svc = DOAJ.authorisationService()
    try:
        auth_svc.can_edit_application(current_user._get_current_object(), ap)
    except exceptions.AuthoriseException:
        abort(401)

    # Edit role is either associate_editor or editor, depending whether the user is group leader
    eg = models.EditorGroup.pull_by_key("name", ap.editor_group)
    role = 'editor' if eg is not None and eg.editor == current_user.id else 'associate_editor'

    if request.method == "GET":
        fc = ApplicationFormFactory.context(role)
        fc.processor(source=ap)
        return fc.render_template(obj=ap)

    elif request.method == "POST":
        fc = ApplicationFormFactory.context(role)

        processor = fc.processor(formdata=request.form)

        if processor.validate():
            try:
                processor.finalise()
                flash('Application updated.', 'success')
                for a in fc.alert:
                    flash_with_url(a, "success")
                return redirect(url_for("editor.application", application_id=ap.id, _anchor='done'))
            except Exception as e:
                flash(str(e))
                return fc.render_template(obj=ap)
        else:
            return fc.render_template(obj=ap)
