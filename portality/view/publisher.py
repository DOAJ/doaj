from flask import Blueprint, request
from flask import render_template, abort, redirect, url_for, flash
from flask.ext.login import current_user, login_required

from portality.core import app
from portality import models, article
from portality.bll import DOAJ
from portality.bll.exceptions import AuthoriseException
from portality.decorators import ssl_required, restrict_to_role, write_required
from portality.formcontext import formcontext
from portality.tasks.ingestarticles import IngestArticlesBackgroundTask, BackgroundException
from portality.view.forms import ArticleForm
from portality.ui.messages import Messages
from huey.exceptions import QueueWriteException

import os, uuid
from time import sleep

blueprint = Blueprint('publisher', __name__)

# restrict everything in admin to logged in users with the "publisher" role
@blueprint.before_request
def restrict():
    return restrict_to_role('publisher')

@blueprint.route("/")
@login_required
@ssl_required
def index():
    return render_template("publisher/index.html", search_page=True, facetviews=["publisher.journals.facetview"])


@blueprint.route("/update_request/<journal_or_suggestion_id>")
@login_required
@ssl_required
@write_required()
def update_request(journal_or_suggestion_id):
    # DOAJ BLL for this request
    dbl = DOAJ()

    # load the application either directly or by crosswalking the journal object
    source = request.values.get("source")
    application = None
    if source == "journal":
        journal = dbl.journal(journal_id=journal_or_suggestion_id)
        try:
            application = dbl.journal_2_application(journal=journal, account=current_user._get_current_object())
        except AuthoriseException as e:
            abort(404)
    else:
        application = dbl.application(application_id=journal_or_suggestion_id)

    # if we didn't find an application or journal, 404 the user
    if application is None:
        abort(404)

    # check to see if the application is editable by the user
    if not dbl.can_edit_update_request(current_user._get_current_object(), application):
        return render_template("publisher/application_already_submitted.html", suggestion=application)

    # if we are requesting the page with a GET, we just want to show the form
    if request.method == "GET":
        fc = dbl.formcontext(type="application", role="publisher", source=application)
        return fc.render_template(edit_suggestion_page=True)

    # if we are requesting the page with a POST, we need to accept the data and handle it
    elif request.method == "POST":
        fc = dbl.formcontext(type="application", role="publisher", form_data=request.form, source=application)
        if fc.validate():
            try:
                fc.finalise()
                Messages.flash(Messages.APPLICATION_UPDATE_SUBMITTED_FLASH)
                for a in fc.alert:
                    Messages.flash_with_url(a, "success")
                Messages.flash(Messages.APPLICATION_UPDATE_CLOSE_TAB_FLASH)
                return redirect(url_for("publisher.update_request", journal_or_suggestion_id=application.id, _anchor='done'))
            except formcontext.FormContextException as e:
                Messages.flash(e.message)
                return redirect(url_for("publisher.update_request", journal_or_suggestion_id=application.id, _anchor='cannot_edit'))
        else:
            return fc.render_template(edit_suggestion_page=True)


@blueprint.route('/progress')
@login_required
@ssl_required
def updates_in_progress():
    return render_template("publisher/updates_in_progress.html", search_page=True, facetviews=["publisher.reapplications.facetview"])

@blueprint.route("/uploadFile", methods=["GET", "POST"])
@blueprint.route("/uploadfile", methods=["GET", "POST"])
@login_required
@ssl_required
@write_required()
def upload_file():
    # all responses involve getting the previous uploads
    previous = models.FileUpload.by_owner(current_user.id)
    
    if request.method == "GET":
        return render_template('publisher/uploadmetadata.html', previous=previous)
    
    # otherwise we are dealing with a POST - file upload or supply of url
    f = request.files.get("file")
    schema = request.values.get("schema")
    url = request.values.get("url")
    
    # file upload takes precedence over URL, in case the user has given us both
    if f.filename != "" and url is not None and url != "":
        flash("You provided a file and a URL - the URL has been ignored")

    try:
        job = IngestArticlesBackgroundTask.prepare(current_user.id, upload_file=f, schema=schema, url=url, previous=previous)
        IngestArticlesBackgroundTask.submit(job)
    except (BackgroundException, QueueWriteException) as e:
        magic = str(uuid.uuid1())
        flash("An error has occurred and your upload may not have succeeded. If the problem persists please report the issue with the ID " + magic)
        app.logger.exception('File upload error. ' + magic)
        return render_template('publisher/uploadmetadata.html', previous=previous)

    if f.filename != "":
        flash("File uploaded and waiting to be processed. Check back here for updates.", "success")
        return render_template('publisher/uploadmetadata.html', previous=previous)
    
    if url is not None and url != "":
        flash("File reference successfully received - it will be processed shortly", "success")
        return render_template('publisher/uploadmetadata.html', previous=previous)
    
    flash("No file or URL provided", "error")
    return render_template('publisher/uploadmetadata.html', previous=previous)

@blueprint.route("/metadata", methods=["GET", "POST"])
@login_required
@ssl_required
@write_required()
def metadata():
    # if this is a get request, give the blank form - there is no edit feature
    if request.method == "GET":
        form = ArticleForm()
        return render_template('publisher/metadata.html', form=form)
    
    # if this is a post request, a form button has been hit and we need to do
    # a bunch of work
    elif request.method == "POST":
        form = ArticleForm(request.form)
        
        # first we need to do any server-side form modifications which
        # the user might request by pressing the add/remove authors buttons
        more_authors = request.values.get("more_authors")
        remove_author = None
        for v in request.values.keys():
            if v.startswith("remove_authors"):
                remove_author = v.split("-")[1]
        
        # if the user wants more authors, add an extra entry
        if more_authors:
            form.authors.append_entry()
            return render_template('publisher/metadata.html', form=form)
        
        # if the user wants to remove an author, do the various back-flips required
        if remove_author is not None:
            keep = []
            while len(form.authors.entries) > 0:
                entry = form.authors.pop_entry()
                if entry.short_name == "authors-" + remove_author:
                    break
                else:
                    keep.append(entry)
            while len(keep) > 0:
                form.authors.append_entry(keep.pop().data)
            return render_template('publisher/metadata.html', form=form)
        
        # if we get to here, then this is the full submission, and we need to
        # validate and return
        enough_authors = _validate_authors(form)
        if form.validate():
            # if the form validates, then we have to do our own bit of validation,
            # which is to check that there is at least one author supplied
            if not enough_authors:
                return render_template('publisher/metadata.html', form=form, author_error=True)
            else:
                xwalk = article.FormXWalk()
                art = xwalk.crosswalk_form(form)
                art.save()
                flash("Article created/updated", "success")
                form = ArticleForm()
                return render_template('publisher/metadata.html', form=form)
        else:
            return render_template('publisher/metadata.html', form=form, author_error=not enough_authors)

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

