from flask import Blueprint, make_response
from flask import render_template, abort
from flask_login import current_user, login_required

from portality.decorators import ssl_required
from portality.bll import DOAJ, exceptions
from portality.util import jsonp

import json

from portality.core import app

# ~~Dashboard:Blueprint~~
blueprint = Blueprint('dashboard', __name__)


@blueprint.route('/')
@login_required
@ssl_required
def top_todo():
    # ~~-> Todo:Service~~
    svc = DOAJ.todoService()
    todos = svc.top_todo(current_user._get_current_object(), size=app.config.get("TODO_LIST_SIZE"))

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


@blueprint.route("/notifications/<notification_id>/seen", methods=["POST"])
@login_required
@ssl_required
@jsonp
def notification_seen(notification_id):
    # ~~-> Notifications:Service
    svc = DOAJ.notificationsService()
    try:
        result = svc.notification_seen(current_user._get_current_object(), notification_id)
    except exceptions.NoSuchObjectException:
        abort(400)

    data = json.dumps({"result" : result})
    resp = make_response(data)
    resp.mimetype = "application/json"
    return resp


@blueprint.route("/notifications")
@login_required
@ssl_required
def notifications():
    # ~~-> Notifications:Page~~
    return render_template("dashboard/notifications.html")
