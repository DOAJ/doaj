from flask import Blueprint
from flask import render_template
from flask_login import current_user, login_required

from portality import models
from portality.decorators import ssl_required, restrict_to_role
from portality.bll import DOAJ

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
