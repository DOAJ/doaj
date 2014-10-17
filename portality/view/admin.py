import json

from flask import Blueprint, request, flash, abort, make_response
from flask import render_template, redirect, url_for
from flask.ext.login import current_user, login_required

from portality.core import app, ssl_required, restrict_to_role
import portality.models as models
from portality.formcontext import formcontext
from portality import lock
from portality.util import flash_with_url

from portality import journal as journal_handler
from portality import suggestion as suggestion_handler
from portality.view.forms import EditorGroupForm

blueprint = Blueprint('admin', __name__)

# restrict everything in admin to logged in users with the "admin" role
@blueprint.before_request
def restrict():
    return restrict_to_role('admin')

# build an admin page where things can be done
@blueprint.route('/')
@login_required
@ssl_required
def index():
    return render_template('admin/index.html', admin_page=True)

@blueprint.route("/journals")
@login_required
@ssl_required
def journals():
    if not current_user.has_role("admin_journals"):
        abort(401)
    return render_template('admin/journals.html',
               search_page=True,
               facetviews=['journals'],
               admin_page=True
           )

@blueprint.route("/article/<article_id>", methods=["POST"])
@login_required
@ssl_required
def article_endpoint(article_id):
    if not current_user.has_role("delete_article"):
        abort(401)
    a = models.Article.pull(article_id)
    if a is None:
        abort(404)
    delete = request.values.get("delete", "false")
    if delete != "true":
        abort(400)
    a.snapshot()
    a.delete()
    # return a json response
    resp = make_response(json.dumps({"success" : True}))
    resp.mimetype = "application/json"
    return resp

@blueprint.route("/journal/<journal_id>", methods=["GET", "POST"])
@login_required
@ssl_required
def journal_page(journal_id):
    return journal_handler.request_handler(request, journal_id, activate_deactivate=True, group_editable=True, editorial_available=True)

@blueprint.route("/journal/<journal_id>/activate", methods=["GET", "POST"])
@login_required
@ssl_required
def journal_activate(journal_id):
    j = journal_handler.get_journal(journal_id)
    if j is None:
        abort(404)
    j.bibjson().active = True
    j.set_in_doaj(True)
    j.save()
    j.propagate_in_doaj_status_to_articles()  # will save each article, could take a while
    return redirect(url_for('.journal_page', journal_id=journal_id))

@blueprint.route("/journal/<journal_id>/deactivate", methods=["GET", "POST"])
@login_required
@ssl_required
def journal_deactivate(journal_id):
    j = journal_handler.get_journal(journal_id)
    if j is None:
        abort(404)
    j.bibjson().active = False
    j.set_in_doaj(False)
    j.save()
    j.propagate_in_doaj_status_to_articles()  # will save each article, could take a while
    return redirect(url_for('.journal_page', journal_id=journal_id))

@blueprint.route("/applications")
@login_required
@ssl_required
def suggestions():
    return render_template('admin/suggestions.html',
               search_page=True,
               facetviews=['suggestions'],
               admin_page=True
           )

@blueprint.route("/suggestion/<suggestion_id>", methods=["GET", "POST"])
@login_required
@ssl_required
def suggestion_page(suggestion_id):
    if not current_user.has_role("edit_suggestion"):
        abort(401)
    ap = models.Suggestion.pull(suggestion_id)
    if ap is None:
        abort(404)

    # attempt to get a lock on the object
    try:
        lockinfo = lock.lock("suggestion", suggestion_id, current_user.id)
    except lock.Locked as l:
        return render_template("admin/suggestion_locked.html", suggestion=ap, lock=l.lock, edit_suggestion_page=True)

    if request.method == "GET":
        fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", source=ap)
        return fc.render_template(edit_suggestion_page=True, lock=lockinfo)
    elif request.method == "POST":
        fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", form_data=request.form, source=ap)
        if fc.validate():
            try:
                fc.finalise()
                flash('Application updated.', 'success')
                for a in fc.alert:
                    flash_with_url(a, "success")
                return redirect(url_for("admin.suggestion_page", suggestion_id=ap.id, _anchor='done'))
            except formcontext.FormContextException as e:
                flash(e.message)
                return redirect(url_for("admin.suggestion_page", suggestion_id=ap.id, _anchor='cannot_edit'))
        else:
            return fc.render_template(edit_suggestion_page=True, lock=lockinfo)

    return suggestion_handler.request_handler(request, suggestion_id, group_editable=True, editorial_available=True, status_options="admin")

@blueprint.route("/admin_site_search")
@login_required
@ssl_required
def admin_site_search():
    return render_template("admin/admin_site_search.html", admin_page=True, search_page=True, facetviews=['admin_journals_and_articles'])

@blueprint.route("/editor_groups")
@login_required
@ssl_required
def editor_group_search():
    return render_template("admin/editor_group_search.html", admin_page=True, search_page=True, facetviews=['editor_group'])

@blueprint.route("/editor_group", methods=["GET", "POST"])
@blueprint.route("/editor_group/<group_id>", methods=["GET", "POST"])
@login_required
@ssl_required
def editor_group(group_id=None):
    if not current_user.has_role("modify_editor_groups"):
        abort(401)

    if request.method == "GET":
        form = EditorGroupForm()
        if group_id is not None:
            eg = models.EditorGroup.pull(group_id)
            form.group_id.data = eg.id
            form.name.data = eg.name
            form.editor.data = eg.editor
            form.associates.data = ",".join(eg.associates)
        return render_template("admin/editor_group.html", admin_page=True, form=form)

    elif request.method == "POST":

        if request.values.get("delete", "false") == "true":
            # we have been asked to delete the id
            if group_id is None:
                # we can only delete things that exist
                abort(400)
            eg = models.EditorGroup.pull(group_id)
            if eg is None:
                abort(404)

            eg.delete()

            # return a json response
            resp = make_response(json.dumps({"success" : True}))
            resp.mimetype = "application/json"
            return resp

        # otherwise, we want to edit the content of the form or the object
        form = EditorGroupForm(request.form)

        if form.validate():
            # get the group id from the url or from the request parameters
            if group_id is None:
                group_id = request.values.get("group_id")
                group_id = group_id if group_id != "" else None

            # if we have a group id, this is an edit, so get the existing group
            if group_id is not None:
                eg = models.EditorGroup.pull(group_id)
                if eg is None:
                    abort(404)
            else:
                eg = models.EditorGroup()

            associates = form.associates.data
            if associates is not None:
                associates = [a.strip() for a in associates.split(",") if a.strip() != ""]

            # prep the user accounts with the correct role(s)
            ed = models.Account.pull(form.editor.data)
            ed.add_role("editor")
            ed.save()
            if associates is not None:
                for a in associates:
                    ae = models.Account.pull(a)
                    ae.add_role("associate_editor")
                    ae.save()

            eg.set_name(form.name.data)
            eg.set_editor(form.editor.data)
            if associates is not None:
                eg.set_associates(associates)
            eg.save()

            flash("Group was updated - changes may not be reflected below immediately.  Reload the page to see the update.", "success")
            return redirect(url_for('admin.editor_group_search'))
        else:
            return render_template("admin/editor_group.html", admin_page=True, form=form)

@blueprint.route("/autocomplete/user")
@login_required
@ssl_required
def user_autocomplete():
    q = request.values.get("q")
    s = request.values.get("s", 10)
    ac = models.Account.autocomplete("id", q, size=s)

    # return a json response
    resp = make_response(json.dumps(ac))
    resp.mimetype = "application/json"
    return resp