from flask import Blueprint, request, make_response, Response
from flask import render_template, abort, redirect, url_for, flash
from flask.ext.login import current_user, login_required

from portality.core import app, ssl_required, restrict_to_role

from portality import models, article
from portality.view.forms import ArticleForm

import os, requests, ftplib
from urlparse import urlparse


blueprint = Blueprint('publisher', __name__)

# restrict everything in admin to logged in users with the "publisher" role
@blueprint.before_request
def restrict():
    return restrict_to_role('publisher')

@blueprint.route("/")
@login_required
@ssl_required
def index():
    return render_template("publisher/index.html", search_page=True, facetviews=["publisher"])

# FIXME: placeholder for actual reapplication page
@blueprint.route("/reapply")
def reapplication_page():
    return make_response("Thank you for your reapplication")

@blueprint.route("/uploadFile", methods=["GET", "POST"])
@blueprint.route("/uploadfile", methods=["GET", "POST"])
@login_required
@ssl_required
def upload_file():
    # all responses involve getting the previous uploads
    previous = models.FileUpload.by_owner(current_user.id)
    
    if request.method == "GET":
        return render_template('publisher/uploadfile.html', previous=previous)
    
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
    return render_template('publisher/uploadfile.html', previous=previous)

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
        return render_template('publisher/uploadfile.html', previous=previous)
        
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
        return render_template('publisher/uploadfile.html', previous=previous)
    
    if actual_schema:
        record.validated(actual_schema)
        record.save()
        previous = [record] + previous # add the new record to the previous records
        flash("File successfully uploaded - it will be processed shortly", "success")
        return render_template('publisher/uploadfile.html', previous=previous)
    else:
        record.failed("File could not be validated against a known schema")
        record.save()
        os.remove(xml)
        previous = [record] + previous
        flash("File could not be validated against a known schema; please fix this before attempting to upload again", "error")
        return render_template('publisher/uploadfile.html', previous=previous)


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
        return __fail(record, previous, error='error while checking submitted file reference: ' + get.status_code)


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
        return render_template('publisher/uploadfile.html', previous=previous)


    def __fail(record, previous, error):
        message = 'The URL could not be accessed; ' + error
        record.failed(message)
        record.save()
        previous = [record] + previous
        flash(message, "error")
        return render_template('publisher/uploadfile.html', previous=previous)


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

    except:
        return __fail(record, previous, error="please check it before submitting again")
    

@blueprint.route("/metadata", methods=["GET", "POST"])
@login_required
@ssl_required
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

