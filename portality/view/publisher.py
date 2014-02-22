from flask import Blueprint, request, abort, make_response, Response
from flask import render_template, abort, redirect, url_for, flash
from flask.ext.login import current_user, login_required

from portality.core import app
from portality import settings, models
from portality import article
import os

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
    if request.method == "GET":
        return render_template('publisher/uploadfile.html')
    
    # otherwise we are dealing with a POST - file upload
    f = request.files.get("file")
    schema = request.values.get("schema")
    
    # do some validation
    if f.filename == "":
        flash("No file provided", "error")
        return render_template('publisher/uploadfile.html')
    
    # prep a record to go into the index, to record this upload
    record = models.FileUpload()
    record.upload(current_user.id, f.filename)
    record.set_id()
    
    # the two file paths that we are going to write to
    xml = os.path.join(app.config.get("UPLOAD_DIR", "."), record.id + ".xml")
    
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
        return render_template('publisher/uploadfile.html')
        
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
        flash("Failed to parse file - it is invalid XML; please fix it before attempting to upload again.", "error")
        return render_template('publisher/uploadfile.html')
    
    if actual_schema:
        record.validated(actual_schema)
        record.save()
        flash("File successfully uploaded - it will be processed shortly", "success")
        return render_template('publisher/uploadfile.html')
    else:
        record.failed("File could not be validated against a known schema")
        record.save()
        os.remove(xml)
        flash("File could not be validated against a known schema; please fix this before attempting to upload again", "error")
        return render_template('publisher/uploadfile.html')
    
    
    
