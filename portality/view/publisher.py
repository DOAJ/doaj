from flask import Blueprint, request, send_from_directory
from flask import render_template, abort, redirect, url_for, flash
from flask.ext.login import current_user, login_required

from portality.core import app
from portality.decorators import ssl_required, restrict_to_role, write_required

from portality import models, article
from portality.view.forms import ArticleForm
from portality.formcontext import formcontext
from portality.util import flash_with_url

import os, requests, ftplib
from urlparse import urlparse
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

@blueprint.route("/reapply/<reapplication_id>", methods=["GET", "POST"])
@login_required
@ssl_required
@write_required
def reapplication_page(reapplication_id):
    if not app.config.get("REAPPLICATION_ACTIVE", False):
        abort(404)

    ap = models.Suggestion.pull(reapplication_id)

    if ap is None:
        abort(404)
    if current_user.id != ap.owner:
        abort(404)
    if not ap.application_status in ["reapplication", "submitted"]:
        return render_template("publisher/application_already_submitted.html", suggestion=ap)

    if request.method == "GET":
        fc = formcontext.ApplicationFormFactory.get_form_context(role="publisher", source=ap)
        return fc.render_template(edit_suggestion_page=True)
    elif request.method == "POST":
        fc = formcontext.ApplicationFormFactory.get_form_context(role="publisher", form_data=request.form, source=ap)
        if fc.validate():
            try:
                fc.finalise()
                flash('Your reapplication has been submitted but it is editable until the DOAJ editorial team picks it up for review.', 'success')
                for a in fc.alert:
                    flash_with_url(a, "success")
                flash("Close this tab to return to your Publisher's Area.", 'success')
                return redirect(url_for("publisher.reapplication_page", reapplication_id=ap.id, _anchor='done'))
            except formcontext.FormContextException as e:
                flash(e.message)
                return redirect(url_for("publisher.reapplication_page", reapplication_id=ap.id, _anchor='cannot_edit'))
        else:
            return fc.render_template(edit_suggestion_page=True)

@blueprint.route('/progress')
@login_required
@ssl_required
def updates_in_progress():
    if not app.config.get("REAPPLICATION_ACTIVE", False):
        abort(404)
    return render_template("publisher/updates_in_progress.html", search_page=True, facetviews=["publisher.reapplications.facetview"])

@blueprint.route("/uploadFile", methods=["GET", "POST"])
@blueprint.route("/uploadfile", methods=["GET", "POST"])
@login_required
@ssl_required
@write_required
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
    
    if f.filename != "":
        return _file_upload(f, schema, previous)
    
    if url is not None and url != "":
        return _url_upload(url, schema, previous)
    
    flash("No file or URL provided", "error")
    return render_template('publisher/uploadmetadata.html', previous=previous)

def _file_upload(f, schema, previous):
    # prep a record to go into the index, to record this upload
    record = models.FileUpload()
    record.upload(current_user.id, f.filename)
    record.set_id()
    
    # the file path that we are going to write to
    xml = os.path.join(app.config.get("UPLOAD_DIR", "."), record.local_filename)
    
    # it's critical here that no errors cause files to get left behind unrecorded
    try:
        # write the incoming file out to the XML file
        f.save(xml)
        
        # save the index entry
        record.save()
    except:
        # if we can't record either of these things, we need to back right off
        try:
            os.remove(xml)
        except:
            pass
        try:
            record.delete()
        except:
            pass
        
        flash("Failed to upload file - please contact an administrator", "error")
        return render_template('publisher/uploadmetadata.html', previous=previous)
        
    # now we have the record in the index and on disk, we can attempt to
    # validate it
    try:
        actual_schema = None
        with open(xml) as handle:
            actual_schema = article.check_schema(handle, schema)
    except:
        # file is a dud, so remove it
        try:
            os.remove(xml)
        except:
            pass
        
        # if we're unable to validate the file, we should record this as
        # a file error.
        record.failed("Unable to parse file")
        record.save()
        previous = [record] + previous
        flash("Failed to parse file - it is invalid XML; please fix it before attempting to upload again.", "error")
        return render_template('publisher/uploadmetadata.html', previous=previous)
    
    if actual_schema:
        record.validated(actual_schema)
        record.save()
        previous = [record] + previous # add the new record to the previous records
        flash("File successfully uploaded - it will be processed shortly", "success")
        return render_template('publisher/uploadmetadata.html', previous=previous)
    else:
        record.failed("File could not be validated against a known schema")
        record.save()
        os.remove(xml)
        previous = [record] + previous
        flash("File could not be validated against a known schema; please fix this before attempting to upload again", "error")
        return render_template('publisher/uploadmetadata.html', previous=previous)


def _url_upload(url, schema, previous):
    # first define a few functions
    def __http_upload(record, previous, url):
        # first thing to try is a head request, supporting redirects
        head = requests.head(url, allow_redirects=True)
        if head.status_code == requests.codes.ok:
            return __ok(record, previous)

        # if we get to here, the head request failed.  This might be because the file
        # isn't there, but it might also be that the server doesn't support HEAD (a lot
        # of webapps [including this one] don't implement it)
        #
        # so we do an interruptable get request instead, so we don't download too much
        # unnecessary content
        get = requests.get(url, stream=True)
        get.close()
        if get.status_code == requests.codes.ok:
            return __ok(previous, record)
        return __fail(record, previous, error='error while checking submitted file reference: {0}'.format(get.status_code))


    def __ftp_upload(record, previous, parsed_url):
        # 1. find out whether the file exists
        # 2. that's it, return OK

        # We might as well check if the file exists using the SIZE command.
        # If the FTP server does not support SIZE, our article ingestion
        # script is going to refuse to process the file anyway, so might as
        # well get a failure now.
        # Also it's more of a faff to check file existence using LIST commands.
        try:
            f = ftplib.FTP(parsed_url.hostname, parsed_url.username, parsed_url.password)
            r = f.sendcmd('TYPE I')  # SIZE is not usually allowed in ASCII mode, so set to binary mode
            if not r.startswith('2'):
                return __fail(record, previous, error='could not set binary '
                    'mode in target FTP server while checking file exists')
            if f.size(parsed_url.path) < 0:
                # this will either raise an error which will get caught below
                # or, very rarely, will return an invalid size
                return __fail(record, previous, error='file does not seem to exist on FTP server')

        except Exception as e:
            return __fail(record, previous, error='error during FTP file existence check: ' + str(e.args))

        return __ok(record, previous)


    def __ok(record, previous):
        record.exists()
        record.save()
        previous = [record] + previous
        flash("File reference successfully received - it will be processed shortly", "success")
        return render_template('publisher/uploadmetadata.html', previous=previous)


    def __fail(record, previous, error):
        message = 'The URL could not be accessed; ' + error
        record.failed(message)
        record.save()
        previous = [record] + previous
        flash(message, "error")
        return render_template('publisher/uploadmetadata.html', previous=previous)


    # prep a record to go into the index, to record this upload.  The filename is the url
    record = models.FileUpload()
    record.upload(current_user.id, url)
    record.set_id()
    record.set_schema(schema) # although it could be wrong, this will get checked later

    # now we attempt to verify that the file is retrievable
    try:
        # first, determine if ftp or http
        parsed_url = urlparse(url)
        if parsed_url.scheme == 'http':
            return __http_upload(record, previous, url)
        elif parsed_url.scheme == 'ftp':
            return __ftp_upload(record, previous, parsed_url)
        else:
            return __fail(record, previous, error='unsupported URL scheme "{0}". Only HTTP and FTP are supported.'.format(parsed_url.scheme))

    except Exception as e:
        return __fail(record, previous, error="please check it before submitting again; " + e.message)
    

@blueprint.route("/metadata", methods=["GET", "POST"])
@login_required
@ssl_required
@write_required
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

@blueprint.route("/reapply", methods=["GET", "POST"])
@login_required
@ssl_required
@write_required
def bulk_reapply():
    if not app.config.get("REAPPLICATION_ACTIVE", False):
        abort(404)

    # User must have bulk reapplications to access this tab
    if not pub_filter_bulk(current_user.id):
        abort(404)

    # Get the download details for reapplication CSVs
    csv_downloads = models.BulkReApplication.by_owner(current_user.id)

    # all responses involve getting the previous uploads
    previous = models.BulkUpload.by_owner(current_user.id)

    if request.method == "GET":
        return render_template("publisher/bulk_reapplication.html", csv_downloads=csv_downloads, previous=previous)

    # otherwise we are dealing with a POST - file upload
    f = request.files.get("file")

    if f.filename != "":
        return _bulk_upload(f)

    flash("No file provided - select a file to upload and try again.", "error")
    return render_template("publisher/bulk_reapplication.html", csv_downloads=csv_downloads, previous=previous)

@blueprint.route('/bulk_download/<filename>')
@login_required
@ssl_required
def bulk_download(filename):
    if not app.config.get("REAPPLICATION_ACTIVE", False):
        abort(404)

    csv_downloads = models.BulkReApplication.by_owner(current_user.id)
    allowed = False
    for c in csv_downloads:
        if c.spreadsheet_name == filename:
            allowed = True
            break

    if allowed:
        try:
            return send_from_directory(app.config.get("BULK_REAPP_PATH"), filename, as_attachment=True)
        except:
            abort(404)
    else:
        abort(404)

def _bulk_upload(f):
    # prep a record to go into the index, to record this upload
    record = models.BulkUpload()
    record.upload(current_user.id, f.filename)
    record.set_id()

    # the file path that we are going to write to
    csv = os.path.join(app.config.get("REAPPLICATION_UPLOAD_DIR", "."), record.local_filename)

    # it's critical here that no errors cause files to get left behind unrecorded
    try:
        # write the incoming file out to the csv file
        f.save(csv)

        # save the index entry
        record.save()

        sleep(2)  # let ES catch up so people can see their file is "in submission" on redirect/refresh
        flash("File successfully uploaded - it will be processed shortly", "success")
        return redirect(url_for('publisher.bulk_reapply'))
    except:
        # if we can't record either of these things, we need to back right off
        try:
            os.remove(csv)
        except:
            pass
        try:
            record.delete()
        except:
            pass

        flash("Failed to upload file - please contact an administrator", "error")
        return redirect(url_for('publisher.bulk_reapply'))


def _validate_authors(form, require=1):
    counted = 0
    for entry in form.authors.entries:
        name = entry.data.get("name")
        if name is not None and name != "":
            counted += 1
    return counted >= require

@blueprint.app_template_filter()
def pub_filter_note(user_id):
    # Only show sticky note if set in config and if user has reapplications
    has_reapps_q = models.OwnerStatusQuery(owner=user_id, statuses=["reapplication", "submitted"], size=0)
    res = models.Suggestion.query(q=has_reapps_q.query())
    count = res.get("hits", {}).get("total", 0)

    return app.config.get("REAPPLICATION_ACTIVE", False) and count > 0

@blueprint.app_template_filter()
def pub_filter_bulk(user_id):
    # only show bulk upload tab if 10+ reapplications
    has_bulk = models.BulkReApplication.count_by_owner(user_id)
    return has_bulk > 0
