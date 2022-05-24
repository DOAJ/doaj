from flask import Blueprint, make_response
from flask import render_template
from flask_login import current_user, login_required

from portality.decorators import ssl_required
from portality.bll import DOAJ
from portality.util import jsonp

import json

# ~~Dashboard:Blueprint~~
blueprint = Blueprint('dashboard', __name__)


@blueprint.route('/')
@login_required
@ssl_required
def top_todo():
    # ~~-> Todo:Service~~
    svc = DOAJ.todoService()
    todos = svc.top_todo(current_user._get_current_object(), size=100)  # FIXME: 100 is probably too large, just using that to get a good view of the data during dev

    # ~~-> Dashboard:Page~~
    return render_template('dashboard/index.html', todos=todos)


@blueprint.route("/top_notifications")
@login_required
@ssl_required
@jsonp
def top_notifications():
    # ~~-> Notifications:Service
    svc = DOAJ.notificationsService()
    notes = svc.top_notifications(current_user._get_current_object(), size=10)

    data = json.dumps([n.data for n in notes])

    resp = make_response(data)
    resp.mimetype = "application/json"
    return resp


@blueprint.route("/notifications")
@login_required
@ssl_required
def notifications():
    return render_template("dashboard/notifications.html")