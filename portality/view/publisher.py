from flask import Blueprint, request, abort, make_response, Response
from flask import render_template, abort, redirect, url_for, flash
from flask.ext.login import current_user, login_required

from portality.core import app

from portality import settings, models
from portality.view.forms import SuggestionForm, countries, country_options_two_char_code_index
from portality import article
import os, requests


blueprint = Blueprint('publisher', __name__)

# restrict everything in admin to logged in users with the "publsiher" role
@blueprint.before_request
def restrict():
    if current_user.is_anonymous() or not current_user.has_role("publisher"):
        abort(401)    

@blueprint.route("/")
@login_required
def index():
    return render_template("publisher/index.html", search_page=True, facetviews=["publisher"])

@blueprint.route("/uploadFile", methods=["GET", "POST"])
@blueprint.route("/uploadfile", methods=["GET", "POST"])
@login_required
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
    # prep a record to go into the index, to record this upload.  The filename is the url
    record = models.FileUpload()
    record.upload(current_user.id, url)
    record.set_id()
    record.set_schema(schema) # although it could be wrong, this will get checked later
    record.save()
    
    # now we attempt to verify that the file is retrievable
    try:
        # first thing to try is a head request, supporting redirects
        head = requests.head(url, allow_redirects=True)
        if head.status_code == requests.codes.ok:
            record.exists()
            record.save()
            previous = [record] + previous
            flash("File reference successfully received - it will be processed shortly", "success")
            return render_template('publisher/uploadfile.html', previous=previous)
        
        # if we get to here, the head request failed.  This might be because the file
        # isn't there, but it might also be that the server doesn't support HEAD (a lot
        # of webapps [including this one] don't implement it)
        #
        # so we do an interruptable get request instead, so we don't download too much
        # unnecessary content
        get = requests.get(url, stream=True)
        get.close()
        if get.status_code == requests.codes.ok:
            record.exists()
            record.save()
            previous = [record] + previous
            flash("File reference successfully received - it will be processed shortly", "success")
            return render_template('publisher/uploadfile.html', previous=previous)
        
    except:
        record.failed("The URL could not be accessed")
        record.save()
        previous = [record] + previous
        flash("The URL provided could not be accessed; please check it before submitting again", "error")
        return render_template('publisher/uploadfile.html', previous=previous)
    
    
@blueprint.route("/suggestion/new", methods=["GET", "POST"])
@login_required
def suggestion():
    form = SuggestionForm(request.form)
    return render_template('publisher/suggestion.html', form=form)
