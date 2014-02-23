from flask import Blueprint, request, abort, make_response, Response
from flask import render_template, abort, redirect, url_for, flash
from flask.ext.login import current_user, login_required

from portality.core import app
from portality import settings
from portality.view.forms import SuggestionForm, countries, country_options_two_char_code_index

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
    publisher = request.values.get("publisher_username")
    
    # do some validation
    if f.filename == "" or publisher is None or publisher == "":
        return render_template('doaj/members/uploadfile.html', no_file=(f.filename == ""), no_publisher=(publisher is None or publisher == ""))
    
    # prep a record to go into the index, to record this upload
    record = models.FileUpload()
    record.upload(f.filename, publisher)
    record.set_id()
    
    # the two file paths that we are going to write to
    txt = os.path.join(app.config.get("UPLOAD_DIR", "."), record.id + ".txt")
    xml = os.path.join(app.config.get("UPLOAD_DIR", "."), record.id + ".xml")
    
    # make the content of the txt metadata file
    metadata = publisher + "\n" + f.filename
    
    # save the metadata to the text file
    with codecs.open(txt, "wb", "utf8") as mdf:
        mdf.write(metadata)
    
    # write the incoming file out to the XML file
    f.save(xml)
    
    # finally, save the index entry
    record.save()
    
    # return a thank you
    flash("File successfully uploaded", "success")
    return render_template('publisher/uploadfile.html')
    
@blueprint.route("/suggestion/new", methods=["GET", "POST"])
@login_required
def suggestion():
    form = SuggestionForm(request.form)
    return render_template('publisher/suggestion.html', form=form)
