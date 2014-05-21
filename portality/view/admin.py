import json

from flask import Blueprint, request, flash, abort, make_response
from flask import render_template, redirect, url_for
from flask.ext.login import current_user, login_required

from portality.core import app, ssl_required, restrict_to_role
import portality.models as models
from portality.suggestion import suggestion_form, SuggestionFormXWalk
from portality import journal as journal_handler
from portality.view.forms import EditSuggestionForm, subjects2str, EditorGroupForm

# from portality.datasets import country_options_two_char_code_index
from portality.lcc import lcc_jstree


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
    s = models.Suggestion.pull(suggestion_id)
    if s is None:
        abort(404)

    current_info = models.ObjectDict(SuggestionFormXWalk.obj2form(s))
    form = EditSuggestionForm(request.form, current_info)

    process_the_form = True
    if request.method == 'POST' and s.application_status == 'accepted':
        flash('You cannot edit suggestions which have been accepted into DOAJ.', 'error')
        process_the_form = False

    # add the contents of a few fields to their descriptions since select2 autocomplete
    # would otherwise obscure the full values
    if form.publisher.data:
        if not form.publisher.description:
            form.publisher.description = 'Full contents: ' + form.publisher.data
        else:
            form.publisher.description += '<br><br>Full contents: ' + form.publisher.data

    if form.society_institution.data:
        if not form.society_institution.description:
            form.society_institution.description = 'Full contents: ' + form.society_institution.data
        else:
            form.society_institution.description += '<br><br>Full contents: ' + form.society_institution.data

    if form.platform.data:
        if not form.platform.description:
            form.platform.description = 'Full contents: ' + form.platform.data
        else:
            form.platform.description += '<br><br>Full contents: ' + form.platform.data

    redirect_url_on_success = url_for('.suggestion_page', suggestion_id=suggestion_id, _anchor='done')
    # meaningless anchor to replace #first_problem used on the form
    # anchors persist between 3xx redirects to the same resource
    # (/application)

    return suggestion_form(form, request, redirect_url_on_success, "admin/suggestion.html",
                           existing_suggestion=s,
                           suggestion=s,
                           process_the_form=process_the_form,
                           admin_page=True,
                           subjectstr=subjects2str(s.bibjson().subjects()),
                           lcc_jstree=json.dumps(lcc_jstree),
    )

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