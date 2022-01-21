from flask import Blueprint, request, flash, abort, make_response
from flask import render_template, redirect, url_for
from flask_login import current_user, login_required
from werkzeug.datastructures import MultiDict
from portality.decorators import ssl_required, restrict_to_role, write_required
from portality.bll import DOAJ

# ~~Dashboard:Blueprint~~
blueprint = Blueprint('dashboard', __name__)


@blueprint.route('/')
@login_required
@ssl_required
def top_todo():
    # ~~-> Todo:Service~~
    svc = DOAJ.todoService()
    todos = svc.top_todo(current_user._get_current_object())
    return render_template('dashboard/top.html', todos=todos)