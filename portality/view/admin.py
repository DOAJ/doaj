import json, re
from collections import namedtuple
from typing import Iterable, List

from flask import Blueprint, request, flash, abort, make_response
from flask import render_template, redirect, url_for, send_file
from flask_login import current_user, login_required
from werkzeug.datastructures import MultiDict

from portality import models
from portality import constants
from portality import dao
from portality import lock
from portality.background import BackgroundSummary
from portality.bll import DOAJ, exceptions
from portality.bll.exceptions import ArticleMergeConflict, DuplicateArticleException
from portality.bll.services.query import Query
from portality.core import app
from portality.crosswalks.application_form import ApplicationFormXWalk
from portality.decorators import ssl_required, restrict_to_role, write_required
from portality.forms.application_forms import ApplicationFormFactory, application_statuses
from portality.forms.application_forms import JournalFormFactory
from portality.forms.article_forms import ArticleFormFactory
from portality.lcc import lcc_jstree
from portality.lib.query_filters import remove_search_limits, update_request, not_update_request
from portality.models import Journal
from portality.tasks import journal_in_out_doaj, journal_bulk_edit, suggestion_bulk_edit, journal_bulk_delete, \
    article_bulk_delete, admin_reports
from portality.ui.messages import Messages
from portality.ui import templates
from portality.util import flash_with_url, jsonp, make_json_resp, get_web_json_payload, validate_json
from portality.view.forms import EditorGroupForm, MakeContinuation
from portality.view.view_helper import exparam_editing_user

# ~~Admin:Blueprint~~
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
    return render_template(templates.ADMIN_JOURNALS_SEARCH, admin_page=True)


@blueprint.route("/journals", methods=["GET"])
@login_required
@ssl_required
def journals():
    qs = request.query_string
    target = url_for("admin.index")
    if qs:
        target += "?" + qs.decode()
    return redirect(target)


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
            app.logger.warning("Bad Request at admin/journals: " + str(request.values.get("q")))
            abort(400)

        # get the total number of journals to be affected
        jtotal = models.Journal.hit_count(query, consistent_order=False)

        # get the total number of articles to be affected
        issns = models.Journal.issns_by_query(query)
        atotal = models.Article.count_by_issns(issns)

        resp = make_response(json.dumps({"journals": jtotal, "articles": atotal}))
        resp.mimetype = "application/json"
        return resp

    elif request.method == "DELETE":
        if not current_user.has_role("delete_article"):
            abort(401)

        try:
            query = json.loads(request.data)
        except:
            app.logger.warning("Bad Request at admin/journals: " + str(request.data))
            abort(400)

        # get only the query part
        query = {"query": query.get("query")}
        models.Journal.delete_selected(query=query, articles=True, snapshot_journals=True, snapshot_articles=True)
        resp = make_response(json.dumps({"status": "success"}))
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
            print(request.values.get("q"))
            abort(400)
        total = models.Article.hit_count(query, consistent_order=False)
        resp = make_response(json.dumps({"total": total}))
        resp.mimetype = "application/json"
        return resp
    elif request.method == "DELETE":
        if not current_user.has_role("delete_article"):
            abort(401)

        try:
            query = json.loads(request.data)
        except:
            app.logger.warning("Bad Request at admin/journals: " + str(request.data))
            abort(400)

        # get only the query part
        query = {"query": query.get("query")}
        models.Article.delete_selected(query=query, snapshot=True)
        resp = make_response(json.dumps({"status": "success"}))
        resp.mimetype = "application/json"
        return resp


@blueprint.route("/delete/article/<article_id>", methods=["POST"])
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
    resp = make_response(json.dumps({"success": True}))
    resp.mimetype = "application/json"
    return resp


@blueprint.route("/article/<article_id>", methods=["GET", "POST"])
@login_required
@ssl_required
@write_required()
def article_page(article_id):
    if not current_user.has_role("edit_article"):
        abort(401)
    ap = models.Article.pull(article_id)
    if ap is None:
        abort(404)

    fc = ArticleFormFactory.get_from_context(role="admin", source=ap, user=current_user)
    if request.method == "GET":
        return fc.render_template()

    elif request.method == "POST":
        user = current_user._get_current_object()
        fc = ArticleFormFactory.get_from_context(role="admin", source=ap, user=user, form_data=request.form)

        fc.modify_authors_if_required(request.values)

        if fc.validate():
            try:
                fc.finalise()
            except ArticleMergeConflict:
                Messages.flash(Messages.ARTICLE_METADATA_MERGE_CONFLICT)
            except DuplicateArticleException:
                Messages.flash(Messages.ARTICLE_METADATA_UPDATE_CONFLICT)

        return fc.render_template()


@blueprint.route("/journal/<journal_id>", methods=["GET", "POST"])
@login_required
@ssl_required
@write_required()
def journal_page(journal_id):
    # ~~JournalForm:Page~~
    auth_svc = DOAJ.authorisationService()
    journal_svc = DOAJ.journalService()

    journal, _ = journal_svc.journal(journal_id)
    if journal is None:
        abort(404)

    try:
        auth_svc.can_edit_journal(current_user._get_current_object(), journal)
    except exceptions.AuthoriseException:
        abort(401)

    # attempt to get a lock on the object
    try:
        lockinfo = lock.lock(constants.LOCK_JOURNAL, journal_id, current_user.id)
    except lock.Locked as l:
        return render_template(templates.JOURNAL_LOCKED, journal=journal, lock=l.lock)

    fc = JournalFormFactory.context("admin", extra_param=exparam_editing_user())
    autochecks = models.Autocheck.for_journal(journal_id)

    if request.method == "GET":
        job = None
        job_id = request.values.get("job")
        if job_id is not None and job_id != "":
            # ~~-> BackgroundJobs:Model~~
            job = models.BackgroundJob.pull(job_id)
            # ~~-> BackgroundJobs:Page~~
            url = url_for("admin.background_jobs_search") + "?source=" + dao.Facetview2.url_encode_query(
                dao.Facetview2.make_query(job_id))
            Messages.flash_with_url(Messages.ADMIN__WITHDRAW_REINSTATE.format(url=url), "success")
        fc.processor(source=journal)

        bibjson = journal.bibjson()
        past_cont_list = create_cont_list(journal.get_past_continuations(), bibjson.replaces)
        future_cont_list = create_cont_list(journal.get_future_continuations(), bibjson.is_replaced_by)

        return fc.render_template(lock=lockinfo, job=job, obj=journal, lcc_tree=lcc_jstree,
                                  past_cont_list=past_cont_list, future_cont_list=future_cont_list,
                                  autochecks=autochecks)

    elif request.method == "POST":
        processor = fc.processor(formdata=request.form, source=journal)
        if processor.validate():
            try:
                processor.finalise()
                flash('Journal updated.', 'success')
                for a in processor.alert:
                    flash_with_url(a, "success")
                return redirect(url_for("admin.journal_page", journal_id=journal.id, _anchor='done'))
            except Exception as e:
                flash(str(e))
                return redirect(url_for("admin.journal_page", journal_id=journal.id, _anchor='cannot_edit'))
        else:
            return fc.render_template(lock=lockinfo, obj=journal, lcc_tree=lcc_jstree, autochecks=autochecks)


@blueprint.route("/journal/readonly/<journal_id>", methods=["GET"])
@login_required
@ssl_required
def journal_readonly(journal_id):
    j = models.Journal.pull(journal_id)
    if j is None:
        abort(404)

    fc = JournalFormFactory.context("admin_readonly")
    fc.processor(source=j)
    return fc.render_template(obj=j, lcc_tree=lcc_jstree, notabs=True)

DisplayContData = namedtuple('DisplayContData', ['issn', 'title', 'id'])


def create_cont_list(continuations: Iterable[Journal],
                     continuation_issns: List[str]) -> List[DisplayContData]:
    def _issn_id_tuple(j: Journal):
        bibjson = j.bibjson()
        return DisplayContData(bibjson.pissn or bibjson.eissn, j.id, bibjson.title)

    cont_list = map(_issn_id_tuple, continuations)
    cont_list = {data.issn: data for data in cont_list}
    cont_list.update({
        issn: DisplayContData(issn, None, None) for issn in continuation_issns
        if issn not in cont_list
    })
    return cont_list.values()


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
@write_required()
def journals_bulk_withdraw():
    payload = get_web_json_payload()
    validate_json(payload, fields_must_be_present=['selection_query'], error_to_raise=BulkAdminEndpointException)

    q = get_query_from_request(payload)
    summary = journal_in_out_doaj.change_by_query(q, False, dry_run=payload.get("dry_run", True))
    return make_json_resp(summary.as_dict(), status_code=200)


@blueprint.route("/journals/bulk/reinstate", methods=["POST"])
@login_required
@ssl_required
@write_required()
def journals_bulk_reinstate():
    payload = get_web_json_payload()
    validate_json(payload, fields_must_be_present=['selection_query'], error_to_raise=BulkAdminEndpointException)

    q = get_query_from_request(payload)
    summary = journal_in_out_doaj.change_by_query(q, True, dry_run=payload.get("dry_run", True))
    return make_json_resp(summary.as_dict(), status_code=200)


#
#####################################################################

@blueprint.route("/journal/<journal_id>/article-info/", methods=["GET"])
@login_required
def journal_article_info(journal_id):
    j = models.Journal.pull(journal_id)
    if j is None:
        abort(404)

    return {'n_articles': models.Article.count_by_issns(j.bibjson().issns(), in_doaj=True)}


@blueprint.route("/journal/<journal_id>/article-info/admin-site-search", methods=["GET"])
@login_required
def journal_article_info_admin_site_search(journal_id):
    j = models.Journal.pull(journal_id)
    if j is None:
        abort(404)

    issns = j.bibjson().issns()
    if not issns:
        abort(404)

    target_url = '/admin/admin_site_search?source={"query":{"bool":{"must":[{"term":{"admin.in_doaj":true}},{"term":{"es_type.exact":"article"}},{"query_string":{"query":"%s","default_operator":"AND","default_field":"index.issn.exact"}}]}},"track_total_hits":true}'
    return redirect(target_url % issns[0].replace('-', r'\\-'))


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
        return render_template(templates.CONTINUATION, form=form, current=j)

    elif request.method == "POST":
        form = MakeContinuation(request.form)
        if not form.validate():
            return render_template(templates.CONTINUATION, form=form, current=j)

        if form.type.data is None:
            abort(400)

        if form.type.data not in ["replaces", "is_replaced_by"]:
            abort(400)

        try:
            cont = j.make_continuation(form.type.data, eissn=form.eissn.data, pissn=form.pissn.data,
                                       title=form.title.data)
        except:
            abort(400)

        flash("The continuation has been created (see below).  You may now edit the other metadata associated with it."
              "  The original journal has also been updated with this continuation's ISSN(s).  "
              "Once you are happy with this record, you can publish it to the DOAJ",
              "success")
        return redirect(url_for('.journal_page', journal_id=cont.id))


@blueprint.route("/applications", methods=["GET"])
@login_required
@ssl_required
def suggestions():
    fc = ApplicationFormFactory.context("admin", extra_param=exparam_editing_user())
    return render_template(templates.APPLICATIONS_SEARCH,
                           admin_page=True,
                           application_status_choices=application_statuses(None, fc))


@blueprint.route("/update_requests", methods=["GET"])
@login_required
@ssl_required
def update_requests():
    fc = ApplicationFormFactory.context("admin", extra_param=exparam_editing_user())
    return render_template(templates.UPDATE_REQUESTS_SEARCH,
                           admin_page=True,
                           application_status_choices=application_statuses(None, fc))


@blueprint.route("/application/<application_id>", methods=["GET", "POST"])
@write_required()
@login_required
@ssl_required
def application(application_id):
    auth_svc = DOAJ.authorisationService()
    application_svc = DOAJ.applicationService()

    ap, _ = application_svc.application(application_id)

    if ap is None:
        abort(404)

    try:
        auth_svc.can_edit_application(current_user._get_current_object(), ap)
    except exceptions.AuthoriseException:
        abort(401)

    try:
        lockinfo = lock.lock(constants.LOCK_APPLICATION, application_id, current_user.id)
    except lock.Locked as l:
        return render_template(templates.APPLICATION_LOCKED, application=ap, lock=l.lock)

    fc = ApplicationFormFactory.context("admin", extra_param=exparam_editing_user())
    form_diff, current_journal = ApplicationFormXWalk.update_request_diff(ap)

    autochecks = models.Autocheck.for_application(application_id)

    if request.method == "GET":
        fc.processor(source=ap)
        return fc.render_template(obj=ap, lock=lockinfo, form_diff=form_diff,
                                  current_journal=current_journal, lcc_tree=lcc_jstree, autochecks=autochecks)

    elif request.method == "POST":
        processor = fc.processor(formdata=request.form, source=ap)
        if processor.validate():
            try:
                processor.finalise(current_user._get_current_object())
                # if (processor.form.resettedFields):
                #     text = "Some fields has been resetted due to invalid value:"
                #     for f in processor.form.resettedFields:
                #         text += "<br>field: {}, invalid value: {}, new value: {}".format(f["name"], f["data"], f["default"])
                #     flash(text, 'info')
                flash('Application updated.', 'success')
                for a in processor.alert:
                    flash_with_url(a, "success")
                return redirect(url_for("admin.application", application_id=ap.id, _anchor='done'))
            except Exception as e:
                flash(str(e))
                return redirect(url_for("admin.application", application_id=ap.id, _anchor='cannot_edit'))
        else:
            return fc.render_template(obj=ap, lock=lockinfo, form_diff=form_diff, current_journal=current_journal,
                                      lcc_tree=lcc_jstree, autochecks=autochecks)


@blueprint.route("/application_quick_reject/<application_id>", methods=["POST"])
@login_required
@ssl_required
@write_required()
def application_quick_reject(application_id):
    # extract the note information from the request
    canned_reason = request.values.get("quick_reject", "")
    additional_info = request.values.get("quick_reject_details", "")
    reasons = []
    if canned_reason != "":
        reasons.append(canned_reason)
    if additional_info != "":
        reasons.append(additional_info)
    if len(reasons) == 0:
        abort(400)
    reason = " - ".join(reasons)
    note = Messages.REJECT_NOTE_WRAPPER.format(editor=current_user.id, note=reason)

    applicationService = DOAJ.applicationService()

    # retrieve the application and an edit lock on that application
    application = None
    try:
        application, alock = applicationService.application(application_id, lock_application=True,
                                                            lock_account=current_user._get_current_object())
    except lock.Locked as e:
        abort(409)

    # determine if this was a new application or an update request
    update_request = application.current_journal is not None
    if update_request:
        abort(400)

    if application.owner is None:
        Messages.flash_with_url(Messages.ADMIN__QUICK_REJECT__NO_OWNER, "error")
        # redirect the user back to the edit page
        return redirect(url_for('.application', application_id=application_id))

    # reject the application
    old_status = application.application_status
    applicationService.reject_application(application, current_user._get_current_object(), note=note)

    # send the notification email to the user
    if old_status != constants.APPLICATION_STATUS_REJECTED:
        eventsSvc = DOAJ.eventsService()
        eventsSvc.trigger(models.Event(constants.EVENT_APPLICATION_STATUS, current_user.id, {
            "application": application.data,
            "old_status": old_status,
            "new_status": constants.APPLICATION_STATUS_REJECTED,
            "process": constants.PROCESS__QUICK_REJECT,
            "note": reason
        }))

    # sort out some flash messages for the user
    flash(note, "success")

    msg = Messages.SENT_REJECTED_APPLICATION_EMAIL_TO_OWNER.format(user=application.owner)
    flash(msg, "success")

    # redirect the user back to the edit page
    return redirect(url_for('.application', application_id=application_id))


@blueprint.route("/admin_site_search", methods=["GET"])
@login_required
@ssl_required
def admin_site_search():
    # edit_formcontext = formcontext.ManEdBulkEdit()
    # edit_form = edit_formcontext.render_template()
    edit_formulaic_context = JournalFormFactory.context("bulk_edit", extra_param=exparam_editing_user())
    edit_form = edit_formulaic_context.render_template()

    return render_template(templates.ADMIN_SITE_SEARCH,
                           admin_page=True,
                           edit_form=edit_form)


@blueprint.route("/editor_groups")
@login_required
@ssl_required
def editor_group_search():
    return render_template(templates.EDITOR_GROUP_SEARCH, admin_page=True)


@blueprint.route("/background_jobs")
@login_required
@ssl_required
def background_jobs_search():
    return render_template(templates.BACKGROUND_JOBS_SEARCH, admin_page=True)


@blueprint.route("/notifications")
@login_required
@ssl_required
def global_notifications_search():
    """ ~~->AdminNotificationsSearch:Page~~ """
    return render_template(templates.GLOBAL_NOTIFICATIONS_SEARCH, admin_page=True)


@blueprint.route("/editor_group", methods=["GET", "POST"])
@blueprint.route("/editor_group/<group_id>", methods=["GET", "POST"])
@login_required
@ssl_required
@write_required()
def editor_group(group_id=None):
    if not current_user.has_role("modify_editor_groups"):
        abort(401)

    # ~~->EditorGroup:Form~~
    if request.method == "GET":
        form = EditorGroupForm()
        if group_id is not None:
            eg = models.EditorGroup.pull(group_id)
            form.group_id.data = eg.id
            form.name.data = eg.name
            # Do not allow the user to edit the name. issue #3859
            form.name.render_kw = {'disabled': True}
            form.maned.data = eg.maned
            form.editor.data = eg.editor
            form.associates.data = ",".join(eg.associates)
        return render_template(templates.EDITOR_GROUP, admin_page=True, form=form)

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
            resp = make_response(json.dumps({"success": True}))
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
                    if ae is not None:  # If the account has been deleted, pull fails
                        ae.add_role("associate_editor")
                        ae.save()

            if eg.name is None:
                eg.set_name(form.name.data)
            eg.set_maned(form.maned.data)
            eg.set_editor(form.editor.data)
            if associates is not None:
                eg.set_associates(associates)
            eg.save()

            flash(
                "Group was updated - changes may not be reflected below immediately.  Reload the page to see the update.",
                "success")
            return redirect(url_for('admin.editor_group_search'))
        else:
            return render_template(templates.EDITOR_GROUP, admin_page=True, form=form)


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


####################################################
## endpoints for bulk edit

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
    elif doaj_type in ['applications', 'update_requests']:
        return suggestion_bulk_edit.suggestion_manage
    else:
        raise BulkAdminEndpointException(
            'Unsupported DOAJ type - you can currently only bulk edit journals and applications/update_requests.')


def get_query_from_request(payload, doaj_type=None):
    q = payload['selection_query']
    q = remove_search_limits(q)

    q = Query(q)

    if doaj_type == "update_requests":
        update_request(q)
    elif doaj_type == "applications":
        not_update_request(q)

    return q.as_dict()


@blueprint.route("/<doaj_type>/bulk/assign_editor_group", methods=["POST"])
@login_required
@ssl_required
@write_required()
def bulk_assign_editor_group(doaj_type):
    task = get_bulk_edit_background_task_manager(doaj_type)

    payload = get_web_json_payload()
    validate_json(payload, fields_must_be_present=['selection_query', 'editor_group'],
                  error_to_raise=BulkAdminEndpointException)

    summary = task(
        selection_query=get_query_from_request(payload, doaj_type),
        editor_group=payload['editor_group'],
        dry_run=payload.get('dry_run', True)
    )

    return make_json_resp(summary.as_dict(), status_code=200)


@blueprint.route("/<doaj_type>/bulk/add_note", methods=["POST"])
@login_required
@ssl_required
@write_required()
def bulk_add_note(doaj_type):
    task = get_bulk_edit_background_task_manager(doaj_type)

    payload = get_web_json_payload()
    validate_json(payload, fields_must_be_present=['selection_query', 'note'],
                  error_to_raise=BulkAdminEndpointException)

    summary = task(
        selection_query=get_query_from_request(payload, doaj_type),
        note=payload['note'],
        dry_run=payload.get('dry_run', True)
    )

    return make_json_resp(summary.as_dict(), status_code=200)


@blueprint.route("/journals/bulk/edit_metadata", methods=["POST"])
@login_required
@ssl_required
@write_required()
def bulk_edit_journal_metadata():
    task = get_bulk_edit_background_task_manager("journals")

    payload = get_web_json_payload()
    if not "metadata" in payload:
        raise BulkAdminEndpointException("key 'metadata' not present in request json")

    formdata = MultiDict(payload["metadata"])
    formulaic_context = JournalFormFactory.context("bulk_edit", extra_param=exparam_editing_user())
    fc = formulaic_context.processor(formdata=formdata)

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


@blueprint.route("/<doaj_type>/bulk/change_status", methods=["POST"])
@login_required
@ssl_required
@write_required()
def applications_bulk_change_status(doaj_type):
    if doaj_type not in ["applications", "update_requests"]:
        abort(403)
    payload = get_web_json_payload()
    validate_json(payload, fields_must_be_present=['selection_query', 'application_status'],
                  error_to_raise=BulkAdminEndpointException)

    q = get_query_from_request(payload, doaj_type)
    summary = get_bulk_edit_background_task_manager('applications')(
        selection_query=q,
        application_status=payload['application_status'],
        dry_run=payload.get('dry_run', True)
    )

    return make_json_resp(summary.as_dict(), status_code=200)


@blueprint.route("/journals/bulk/delete", methods=['POST'])
@write_required()
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
@write_required()
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

#################################################

################################################
## Reporting endpoint

@blueprint.route("/report", methods=["POST"])
@write_required()
@login_required
def request_report():
    model = request.values.get("model")
    query_raw = request.values.get("query")
    name = request.values.get("name")
    # TODO: it's probably a bit cheeky to use the type param (used for casting) to run our lambda function, but it works
    notes = request.values.get("notes", False, lambda x: json.loads(x))

    if notes is True and not current_user.has_role(constants.ROLE_ADMIN_REPORT_WITH_NOTES): # "ultra_admin_reports_with_notes"
        # Fixme: this abort is only visible within the network console, because it's a jSON endpoint to serve the page.
        # It will just appear that the generate button isn't working (but they'll have edited the HTML to re-enable the checkbox)
        abort(403)

    query = json.loads(query_raw)
    sane_query = {"query": query.get("query")}
    if "sort" in query:
        sane_query["sort"] = query["sort"]

    model_endpoint_map = {
        "journal": "journal",
        "application": "suggestion"
    }

    query_svc = DOAJ.queryService()
    real_query = query_svc.make_actionable_query("admin_query", model_endpoint_map.get(model), current_user, sane_query)

    job = admin_reports.AdminReportsBackgroundTask.prepare(current_user.id, model=model, true_query=real_query.as_dict(), ui_query=sane_query, name=name, notes=notes)
    admin_reports.AdminReportsBackgroundTask.submit(job)

    return make_json_resp({"job_id": job.id}, status_code=200)


@blueprint.route("/report/<report_id>", methods=["GET"])
@login_required
def get_report(report_id):
    def safe(filename):
        return re.sub(r'[^a-zA-Z0-9-_]', '_', filename)

    exporter = DOAJ.exportService()
    record, fh = exporter.retrieve(report_id)
    safe_filename = safe(record.name) + "_" + safe(record.generated_date) + ".csv"
    return send_file(fh, as_attachment=True, download_name=safe_filename)

@blueprint.route("/reports", methods=["GET"])
@login_required
def reports_search():
    return render_template(templates.ADMIN_REPORTS_SEARCH)