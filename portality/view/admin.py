import json

from flask import Blueprint, request, flash, abort, make_response
from flask import render_template, redirect, url_for
from flask_login import current_user, login_required

from werkzeug.datastructures import MultiDict

from portality.decorators import ssl_required, restrict_to_role, write_required
import portality.models as models

from portality.formcontext import formcontext, choices
from portality import lock, app_email
from portality.lib.es_query_http import remove_search_limits
from portality.util import flash_with_url, jsonp, make_json_resp, get_web_json_payload, validate_json
from portality.core import app
from portality.tasks import journal_in_out_doaj, journal_bulk_edit, suggestion_bulk_edit, journal_bulk_delete, article_bulk_delete
from portality.bll.doaj import DOAJ
from portality.formcontext import emails
from portality.ui.messages import Messages

from portality.view.forms import EditorGroupForm, MakeContinuation
from portality.background import BackgroundSummary

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


@blueprint.route("/journals", methods=["GET"])
@login_required
@ssl_required
def journals():
    if not current_user.has_role("admin_journals"):
        abort(401)
    return render_template('admin/journals.html',
               search_page=True,
               facetviews=['admin.journals.facetview'],
               admin_page=True
           )


@blueprint.route("/journals", methods=["POST", "DELETE"])
@login_required
@ssl_required
@write_required()
@jsonp
def journals_list():
    if request.method == "POST":
        try:
            query = json.loads(request.values.get("q"))
        except:
            app.logger.warn("Bad Request at admin/journals: " + str(request.values.get("q")))
            abort(400)

        # get the total number of journals to be affected
        jtotal = models.Journal.hit_count(query, consistent_order=False)

        # get the total number of articles to be affected
        issns = models.Journal.issns_by_query(query)
        atotal = models.Article.count_by_issns(issns)

        resp = make_response(json.dumps({"journals" : jtotal, "articles" : atotal}))
        resp.mimetype = "application/json"
        return resp

    elif request.method == "DELETE":
        if not current_user.has_role("delete_article"):
            abort(401)

        try:
            query = json.loads(request.data)
        except:
            app.logger.warn("Bad Request at admin/journals: " + str(request.data))
            abort(400)

        # get only the query part
        query = {"query" : query.get("query")}
        models.Journal.delete_selected(query=query, articles=True, snapshot_journals=True, snapshot_articles=True)
        resp = make_response(json.dumps({"status" : "success"}))
        resp.mimetype = "application/json"
        return resp


@blueprint.route("/articles", methods=["POST", "DELETE"])
@login_required
@ssl_required
@write_required()
@jsonp
def articles_list():
    if request.method == "POST":
        try:
            query = json.loads(request.values.get("q"))
        except:
            print request.values.get("q")
            abort(400)
        total = models.Article.hit_count(query, consistent_order=False)
        resp = make_response(json.dumps({"total" : total}))
        resp.mimetype = "application/json"
        return resp
    elif request.method == "DELETE":
        if not current_user.has_role("delete_article"):
            abort(401)

        try:
            query = json.loads(request.data)
        except:
            app.logger.warn("Bad Request at admin/journals: " + str(request.data))
            abort(400)

        # get only the query part
        query = {"query" : query.get("query")}
        models.Article.delete_selected(query=query, snapshot=True)
        resp = make_response(json.dumps({"status" : "success"}))
        resp.mimetype = "application/json"
        return resp


@blueprint.route("/article/<article_id>", methods=["POST"])
@login_required
@ssl_required
@write_required()
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
@write_required()
def journal_page(journal_id):
    if not current_user.has_role("edit_journal"):
        abort(401)
    ap = models.Journal.pull(journal_id)
    if ap is None:
        abort(404)

    # attempt to get a lock on the object
    try:
        lockinfo = lock.lock("journal", journal_id, current_user.id)
    except lock.Locked as l:
        return render_template("admin/journal_locked.html", journal=ap, lock=l.lock, edit_journal_page=True)

    if request.method == "GET":
        job = None
        job_id = request.values.get("job")
        if job_id is not None and job_id != "":
            job = models.BackgroundJob.pull(job_id)
        fc = formcontext.JournalFormFactory.get_form_context(role="admin", source=ap)
        return fc.render_template(edit_journal_page=True, lock=lockinfo, job=job)
    elif request.method == "POST":
        fc = formcontext.JournalFormFactory.get_form_context(role="admin", form_data=request.form, source=ap)
        if fc.validate():
            try:
                fc.finalise()
                flash('Journal updated.', 'success')
                for a in fc.alert:
                    flash_with_url(a, "success")
                return redirect(url_for("admin.journal_page", journal_id=ap.id, _anchor='done'))
            except formcontext.FormContextException as e:
                flash(e.message)
                return redirect(url_for("admin.journal_page", journal_id=ap.id, _anchor='cannot_edit'))
        else:
            return fc.render_template(edit_journal_page=True, lock=lockinfo)

######################################################
# Endpoints for reinstating/withdrawing journals from the DOAJ
#

@blueprint.route("/journal/<journal_id>/activate", methods=["GET", "POST"])
@login_required
@ssl_required
@write_required()
def journal_activate(journal_id):
    job = journal_in_out_doaj.change_in_doaj([journal_id], True)
    return redirect(url_for('.journal_page', journal_id=journal_id, job=job.id))


@blueprint.route("/journal/<journal_id>/deactivate", methods=["GET", "POST"])
@login_required
@ssl_required
@write_required()
def journal_deactivate(journal_id):
    job = journal_in_out_doaj.change_in_doaj([journal_id], False)
    return redirect(url_for('.journal_page', journal_id=journal_id, job=job.id))


@blueprint.route("/journals/bulk/withdraw", methods=["POST"])
@login_required
@ssl_required
def journals_bulk_withdraw():
    payload = get_web_json_payload()
    validate_json(payload, fields_must_be_present=['selection_query'], error_to_raise=BulkAdminEndpointException)

    q = get_query_from_request(payload)
    summary = journal_in_out_doaj.change_by_query(q, False, dry_run=payload.get("dry_run", True))
    return make_json_resp(summary.as_dict(), status_code=200)

@blueprint.route("/journals/bulk/reinstate", methods=["POST"])
@login_required
@ssl_required
def journals_bulk_reinstate():
    payload = get_web_json_payload()
    validate_json(payload, fields_must_be_present=['selection_query'], error_to_raise=BulkAdminEndpointException)

    q = get_query_from_request(payload)
    summary = journal_in_out_doaj.change_by_query(q, True, dry_run=payload.get("dry_run", True))
    return make_json_resp(summary.as_dict(), status_code=200)

#
#####################################################################

@blueprint.route("/journal/<journal_id>/continue", methods=["GET", "POST"])
@login_required
@ssl_required
@write_required()
def journal_continue(journal_id):
    j = models.Journal.pull(journal_id)
    if j is None:
        abort(404)

    if request.method == "GET":
        type = request.values.get("type")
        form = MakeContinuation()
        form.type.data = type
        return render_template("admin/continuation.html", form=form, current=j)

    elif request.method == "POST":
        form = MakeContinuation(request.form)
        if not form.validate():
            return render_template('admin/continuation.html', form=form, current=j)

        if form.type.data is None:
            abort(400)

        if form.type.data not in ["replaces", "is_replaced_by"]:
            abort(400)

        try:
            cont = j.make_continuation(form.type.data, eissn=form.eissn.data, pissn=form.pissn.data, title=form.title.data)
        except:
            abort(400)

        flash("The continuation has been created (see below).  You may now edit the other metadata associated with it.  The original journal has also been updated with this continuation's ISSN(s).  Once you are happy with this record, you can publish it to the DOAJ", "success")
        return redirect(url_for('.journal_page', journal_id=cont.id))


@blueprint.route("/applications", methods=["GET"])
@login_required
@ssl_required
def suggestions():
    return render_template("admin/suggestions.html",
                           admin_page=True, search_page=True,
                           facetviews=['admin.applications.facetview'],
                           application_status_choices=choices.Choices.application_status("admin"))


@blueprint.route("/suggestion/<suggestion_id>", methods=["GET", "POST"])
@login_required
@ssl_required
@write_required()
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


@blueprint.route("/application_quick_reject/<application_id>", methods=["POST"])
@login_required
@ssl_required
@write_required()
def application_quick_reject(application_id):
    applicationService = DOAJ.applicationService()
    # retrieve the application and an edit lock on that application
    application = None
    try:
        application, alock = doaj.application(application_id, lock_application=True, lock_account=current_user._get_current_object())
    except lock.Locked as e:
        abort(409)

    # extract the note information from the request
    reason = request.values.get("reject_reason")
    if reason == "":
        reason = request.values.get("custom_reject_reason")
    if reason == "":
        abort(400)
    note = Messages.REJECT_NOTE_WRAPPER.format(note=reason)

    # determine if this was a new application or an update request, for use later
    update_request = application.current_journal is not None

    # reject the application
    doaj.reject_application(application, current_user._get_current_object(), note=note)

    # send the notification email to the user
    sent = False
    try:
        emails.send_publisher_reject_email(application, note=reason, update_request=update_request)
        sent = True
    except app_email.EmailException as e:
        pass

    # sort out some flash messages for the user
    flash(note, "success")

    if sent:
        msg = Messages.SENT_REJECTED_APPLICATION_EMAIL
        if update_request:
            msg = Messages.SENT_REJECTED_UPDATE_REQUEST_EMAIL
    else:
        msg = Messages.NOT_SENT_REJECTED_APPLICATION_EMAIL
        if update_request:
            msg = Messages.NOT_SENT_REJECTED_UPDATE_REQUEST_EMAIL

    publisher_email = application.get_latest_contact_email()
    msg = msg.format(email=publisher_email)
    flash(msg, "success")

    # redirect the user back to the edit page
    return redirect(url_for('.suggestion_page', suggestion_id=application_id))


@blueprint.route("/admin_site_search", methods=["GET"])
@login_required
@ssl_required
def admin_site_search():
    edit_formcontext = formcontext.ManEdBulkEdit()
    edit_form = edit_formcontext.render_template()

    return render_template("admin/admin_site_search.html",
                           admin_page=True, search_page=True,
                           facetviews=['admin.journalarticle.facetview'],
                           edit_form=edit_form)


@blueprint.route("/editor_groups")
@login_required
@ssl_required
def editor_group_search():
    return render_template("admin/editor_group_search.html", admin_page=True, search_page=True, facetviews=['admin.editorgroups.facetview'])

@blueprint.route("/background_jobs")
@login_required
@ssl_required
def background_jobs_search():
    return render_template("admin/background_jobs_search.html", admin_page=True, search_page=True, facetviews=['admin.background_jobs.facetview'])

@blueprint.route("/editor_group", methods=["GET", "POST"])
@blueprint.route("/editor_group/<group_id>", methods=["GET", "POST"])
@login_required
@ssl_required
@write_required()
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


# Route which returns the associate editor account names within a given editor group
@blueprint.route("/dropdown/eg_associates")
@login_required
@ssl_required
def eg_associates_dropdown():
    egn = request.values.get("egn")
    eg = models.EditorGroup.pull_by_key("name", egn)

    if eg is not None:
        editors = [eg.editor]
        editors += eg.associates
        editors = list(set(editors))
    else:
        editors = None

    # return a json response
    resp = make_response(json.dumps(editors))
    resp.mimetype = "application/json"
    return resp


class BulkAdminEndpointException(Exception):
    pass


@app.errorhandler(BulkAdminEndpointException)
def bulk_admin_endpoints_bad_request(exception):
    r = {}
    r['error'] = exception.message
    return make_json_resp(r, status_code=400)


def get_bulk_edit_background_task_manager(doaj_type):
    if doaj_type == 'journals':
        return journal_bulk_edit.journal_manage
    elif doaj_type == 'applications':
        return suggestion_bulk_edit.suggestion_manage
    else:
        raise BulkAdminEndpointException('Unsupported DOAJ type - you can currently only bulk edit journals and applications.')


def get_query_from_request(payload):
    q = payload['selection_query']
    q = remove_search_limits(q)
    return q


@blueprint.route("/<doaj_type>/bulk/assign_editor_group", methods=["POST"])
@login_required
@ssl_required
def bulk_assign_editor_group(doaj_type):
    task = get_bulk_edit_background_task_manager(doaj_type)

    payload = get_web_json_payload()
    validate_json(payload, fields_must_be_present=['selection_query', 'editor_group'], error_to_raise=BulkAdminEndpointException)

    summary = task(
        selection_query=get_query_from_request(payload),
        editor_group=payload['editor_group'],
        dry_run=payload.get('dry_run', True)
    )

    return make_json_resp(summary.as_dict(), status_code=200)


@blueprint.route("/<doaj_type>/bulk/add_note", methods=["POST"])
@login_required
@ssl_required
def bulk_add_note(doaj_type):
    task = get_bulk_edit_background_task_manager(doaj_type)

    payload = get_web_json_payload()
    validate_json(payload, fields_must_be_present=['selection_query', 'note'], error_to_raise=BulkAdminEndpointException)

    summary = task(
        selection_query=get_query_from_request(payload),
        note=payload['note'],
        dry_run=payload.get('dry_run', True)
    )

    return make_json_resp(summary.as_dict(), status_code=200)

@blueprint.route("/journals/bulk/edit_metadata", methods=["POST"])
@login_required
@ssl_required
def bulk_edit_journal_metadata():
    task = get_bulk_edit_background_task_manager("journals")

    payload = get_web_json_payload()
    if not "metadata" in payload:
        raise BulkAdminEndpointException("key 'metadata' not present in request json")

    formdata = MultiDict(payload["metadata"])
    fc = formcontext.JournalFormFactory.get_form_context(
        role="bulk_edit",
        form_data=formdata
    )
    if not fc.validate():
        msg = "Unable to submit your request due to form validation issues: "
        for field in fc.form:
            if field.errors:
                msg += field.label.text + " - " + ",".join(field.errors)
        summary = BackgroundSummary(None, error=msg)
    else:
        summary = task(
            selection_query=get_query_from_request(payload),
            dry_run=payload.get('dry_run', True),
            **payload["metadata"]
        )

    return make_json_resp(summary.as_dict(), status_code=200)


@blueprint.route("/applications/bulk/change_status", methods=["POST"])
@login_required
@ssl_required
def applications_bulk_change_status():
    payload = get_web_json_payload()
    validate_json(payload, fields_must_be_present=['selection_query', 'application_status'], error_to_raise=BulkAdminEndpointException)

    q = get_query_from_request(payload)
    summary = get_bulk_edit_background_task_manager('applications')(
        selection_query=q,
        application_status=payload['application_status'],
        dry_run=payload.get('dry_run', True)
    )

    return make_json_resp(summary.as_dict(), status_code=200)


@blueprint.route("/journals/bulk/delete", methods=['POST'])
def bulk_journals_delete():
    if not current_user.has_role("ultra_bulk_delete"):
        abort(403)
    payload = get_web_json_payload()
    validate_json(payload, fields_must_be_present=['selection_query'], error_to_raise=BulkAdminEndpointException)

    q = get_query_from_request(payload)
    summary = journal_bulk_delete.journal_bulk_delete_manage(
        selection_query=q,
        dry_run=payload.get('dry_run', True)
    )
    return make_json_resp(summary.as_dict(), status_code=200)


@blueprint.route("/articles/bulk/delete", methods=['POST'])
def bulk_articles_delete():
    if not current_user.has_role("ultra_bulk_delete"):
        abort(403)
    payload = get_web_json_payload()
    validate_json(payload, fields_must_be_present=['selection_query'], error_to_raise=BulkAdminEndpointException)

    q = get_query_from_request(payload)
    summary = article_bulk_delete.article_bulk_delete_manage(
        selection_query=q,
        dry_run=payload.get('dry_run', True)
    )

    return make_json_resp(summary.as_dict(), status_code=200)
