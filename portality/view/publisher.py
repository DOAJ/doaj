from flask import Blueprint, request, make_response
from flask import render_template, abort, redirect, url_for, flash
from flask_login import current_user, login_required

from portality.core import app
from portality import models
from portality.bll import DOAJ
from portality.bll.exceptions import AuthoriseException, ArticleMergeConflict, DuplicateArticleException
from portality.decorators import ssl_required, restrict_to_role, write_required
from portality.formcontext import formcontext
from portality.tasks.ingestarticles import IngestArticlesBackgroundTask, BackgroundException
from portality.ui.messages import Messages
from portality import lock
from portality.models import DraftApplication

from huey.exceptions import TaskException

import uuid

blueprint = Blueprint('publisher', __name__)

# restrict everything in admin to logged in users with the "publisher" role
@blueprint.before_request
def restrict():
    return restrict_to_role('publisher')

@blueprint.route("/")
@login_required
@ssl_required
def index():
    return render_template("publisher/index.html")


@blueprint.route("/journal")
@login_required
@ssl_required
def journals():
    return render_template("publisher/journals.html")


@blueprint.route("/application/<application_id>/delete", methods=["GET"])
def delete_application(application_id):
    # if this is a draft application, we can just remove it
    draft_application = DraftApplication.pull(application_id)
    if draft_application is not None:
        draft_application.delete()
        return redirect(url_for("publisher.deleted_thanks"))

    # otherwise delegate to the application service to sort this out
    appService = DOAJ.applicationService()
    appService.delete_application(application_id, current_user._get_current_object())

    return redirect(url_for("publisher.deleted_thanks"))


@blueprint.route("/application/deleted")
def deleted_thanks():
    return render_template("layouts/static_page.html", page_frag="publisher/application_deleted.html")


@blueprint.route("/update_request/<journal_id>", methods=["GET", "POST", "DELETE"])
@login_required
@ssl_required
@write_required()
def update_request(journal_id):
    # DOAJ BLL for this request
    journalService = DOAJ.journalService()
    applicationService = DOAJ.applicationService()

    # if this is a delete request, deal with it first and separately from the below logic
    if request.method == "DELETE":
        journal, _ = journalService.journal(journal_id)
        application_id = journal.current_application
        if application_id is not None:
            applicationService.delete_application(application_id, current_user._get_current_object())
        else:
            abort(404)
        return ""

    # load the application either directly or by crosswalking the journal object
    application = None
    jlock = None
    alock = None
    try:
        application, jlock, alock = applicationService.update_request_for_journal(journal_id, account=current_user._get_current_object())
    except AuthoriseException as e:
        if e.reason == AuthoriseException.WRONG_STATUS:
            journal, _ = journalService.journal(journal_id)
            return render_template("publisher/application_already_submitted.html", journal=journal)
        else:
            abort(404)
    except lock.Locked as e:
        journal, _ = journalService.journal(journal_id)
        return render_template("publisher/locked.html", journal=journal, lock=e.lock)

    # if we didn't find an application or journal, 404 the user
    if application is None:
        if jlock is not None: jlock.delete()
        if alock is not None: alock.delete()
        abort(404)

    # if we have a live application and cancel was hit, then cancel the operation and redirect
    # first determine if this is a cancel request on the form
    cancelled = request.values.get("cancel")
    if cancelled is not None:
        if jlock is not None: jlock.delete()
        if alock is not None: alock.delete()
        return redirect(url_for("publisher.updates_in_progress"))

    # if we are requesting the page with a GET, we just want to show the form
    if request.method == "GET":
        fc = formcontext.ApplicationFormFactory.get_form_context(role="publisher", source=application)
        return fc.render_template(edit_suggestion_page=True)

    # if we are requesting the page with a POST, we need to accept the data and handle it
    elif request.method == "POST":
        fc = formcontext.ApplicationFormFactory.get_form_context(role="publisher", form_data=request.form, source=application)
        if fc.validate():
            try:
                fc.finalise()
                Messages.flash(Messages.APPLICATION_UPDATE_SUBMITTED_FLASH)
                for a in fc.alert:
                    Messages.flash_with_url(a, "success")
                return redirect(url_for("publisher.updates_in_progress"))
            except formcontext.FormContextException as e:
                Messages.flash(str(e))
                return redirect(url_for("publisher.update_request", journal_id=journal_id, _anchor='cannot_edit'))
            finally:
                if jlock is not None: jlock.delete()
                if alock is not None: alock.delete()
        else:
            return fc.render_template(edit_suggestion_page=True)


@blueprint.route("/view_update_request/<application_id>", methods=["GET", "POST"])
@login_required
@ssl_required
@write_required()
def update_request_readonly(application_id):
    # DOAJ BLL for this request
    applicationService = DOAJ.applicationService()
    authService = DOAJ.authorisationService()

    application, _ = applicationService.application(application_id)
    try:
        authService.can_view_application(current_user._get_current_object(), application)
    except AuthoriseException as e:
        abort(404)

    fc = formcontext.ApplicationFormFactory.get_form_context(role="update_request_readonly", source=application)
    return fc.render_template(no_sidebar=True)

@blueprint.route('/progress')
@login_required
@ssl_required
def updates_in_progress():
    return render_template("publisher/updates_in_progress.html")


@blueprint.route("/uploadfile", methods=["GET", "POST"])
@login_required
@ssl_required
@write_required()
def upload_file():
    # all responses involve getting the previous uploads
    previous = models.FileUpload.by_owner(current_user.id)

    if request.method == "GET":
        schema = request.cookies.get("schema")
        if schema is None:
            schema = ""
        return render_template('publisher/uploadmetadata.html', previous=previous, schema=schema)
    
    # otherwise we are dealing with a POST - file upload or supply of url
    f = request.files.get("file")
    schema = request.values.get("schema")
    url = request.values.get("url")
    resp = make_response(redirect(url_for("publisher.upload_file")))
    resp.set_cookie("schema", schema)

    # file upload takes precedence over URL, in case the user has given us both
    if f is not None and f.filename != "" and url is not None and url != "":
        flash("You provided a file and a URL - the URL has been ignored")

    try:
        job = IngestArticlesBackgroundTask.prepare(current_user.id, upload_file=f, schema=schema, url=url, previous=previous)
        IngestArticlesBackgroundTask.submit(job)
    except (BackgroundException, TaskException) as e:
        magic = str(uuid.uuid1())
        flash("An error has occurred and your upload may not have succeeded. If the problem persists please report the issue with the ID " + magic)
        app.logger.exception('File upload error. ' + magic)
        return resp

    if f is not None and f.filename != "":
        flash("File uploaded and waiting to be processed. Check back here for updates.", "success")
        return resp
    
    if url is not None and url != "":
        flash("File reference successfully received - it will be processed shortly", "success")
        return resp
    
    flash("No file or URL provided", "error")
    return resp

@blueprint.route("/metadata", methods=["GET", "POST"])
@login_required
@ssl_required
@write_required()
def metadata():
    user = current_user._get_current_object()
    # if this is a get request, give the blank form - there is no edit feature
    if request.method == "GET":
        fc = formcontext.ArticleFormFactory.get_from_context(user=user, role="publisher")
        return fc.render_template()
    
    # if this is a post request, a form button has been hit and we need to do
    # a bunch of work
    elif request.method == "POST":

        fc = formcontext.ArticleFormFactory.get_from_context(role="publisher", user=user,
                                                             form_data=request.form)
        # first we need to do any server-side form modifications which
        # the user might request by pressing the add/remove authors buttons

        fc.modify_authors_if_required(request.values)

        validated = False
        if fc.validate():
            try:
                fc.finalise()
                validated = True
            except ArticleMergeConflict:
                Messages.flash(Messages.ARTICLE_METADATA_MERGE_CONFLICT)
            except DuplicateArticleException:
                Messages.flash(Messages.ARTICLE_METADATA_UPDATE_CONFLICT)

        return fc.render_template(validated=validated)


@blueprint.route("/help")
@login_required
@ssl_required
def help():
    return render_template("publisher/help.html")


def _validate_authors(form, require=1):
    counted = 0
    for entry in form.authors.entries:
        name = entry.data.get("name")
        if name is not None and name != "":
            counted += 1
    return counted >= require

