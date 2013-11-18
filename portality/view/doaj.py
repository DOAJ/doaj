from flask import Blueprint, request, abort, make_response
from flask import render_template, abort
from flask.ext.login import current_user

from portality import models as models
from portality.core import app


blueprint = Blueprint('doaj', __name__)

@blueprint.route("/")
def home():
    return render_template('doaj/index.html')
