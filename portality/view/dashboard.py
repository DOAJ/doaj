from flask import Blueprint
from flask import render_template
from flask_login import current_user, login_required

from portality import models
from portality.decorators import ssl_required
from portality.bll import DOAJ

# ~~Dashboard:Blueprint~~
blueprint = Blueprint('dashboard', __name__)


@blueprint.route('/')
@login_required
@ssl_required
def top_todo():
    # ~~-> Todo:Service~~
    svc = DOAJ.todoService()
    todos = svc.top_todo(current_user._get_current_object(), size=5)  # FIXME: 5 is just to shrink the page section down to make it easier to work on the activity area underneath

    # ~~-> Dashboard:Page~~
    return render_template('dashboard/index.html', todos=todos)
