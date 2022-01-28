from flask import Blueprint
from flask import render_template
from flask_login import current_user, login_required
from portality.decorators import ssl_required, restrict_to_role
from portality.bll import DOAJ

# ~~Dashboard:Blueprint~~
blueprint = Blueprint('dashboard', __name__)


@blueprint.route('/')
@login_required
@ssl_required
def top_todo():
    # ~~-> Todo:Service~~
    svc = DOAJ.todoService()
    todos = svc.top_todo(current_user._get_current_object(), size=100)  # FIXME: 100 is probably too large, just using that to get a good view of the data during dev
    return render_template('dashboard/top.html', todos=todos)