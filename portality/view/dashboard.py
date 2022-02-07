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
    todos = svc.top_todo(current_user._get_current_object(), size=100)  # FIXME: 100 is probably too large, just using that to get a good view of the data during dev

    # ~~-> EditorGroup:Model ~~
    egs = []
    if current_user.has_role("admin"):
        egs = [e for e in models.EditorGroup.groups_by_maned(current_user.id)]

    # ~~-> Dashboard:Page~~
    return render_template('dashboard/index.html', todos=todos, maned_of=egs)
