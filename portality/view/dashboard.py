from flask import Blueprint, make_response
from flask import render_template, abort, request
from flask_login import current_user, login_required

from portality.decorators import ssl_required
from portality.bll import DOAJ, exceptions
from portality.util import jsonp
from portality.ui import templates

import json

from portality.core import app

# ~~Dashboard:Blueprint~~
blueprint = Blueprint('dashboard', __name__)


@blueprint.route('/')
@login_required
@ssl_required
def top_todo():
    filter = request.values.get("filter")
    new_applications, update_requests, on_hold, flag = True, True, True, False
    if filter == "na":
        on_hold = False
        update_requests = False
    elif filter == "ur":
        on_hold = False
        new_applications = False
    elif filter == "oh":
        update_requests = False
        new_applications = False
    elif filter == "flag":
        new_applications = False
        update_requests = False
        on_hold = False
        flag = True


    # ~~-> Todo:Service~~
    svc = DOAJ.todoService()
    todos = svc.top_todo(current_user._get_current_object(),
                         size=app.config.get("TODO_LIST_SIZE"),
                         new_applications=new_applications,
                         update_requests=update_requests,
                         flag=flag,
                         on_hold=on_hold)

    count = svc.user_finished_historical_counts(current_user._get_current_object())

    # ~~-> Dashboard:Page~~
    return render_template(templates.DASHBOARD, todos=todos, historical_count=count)


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
    return render_template(templates.NOTIFICATIONS)
