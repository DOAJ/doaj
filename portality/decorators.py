from functools import wraps
from flask import request, abort, redirect, flash, url_for, render_template
from flask.ext.login import current_user
from flask_login import login_user

from portality.api.v1.common import Api401Error

from portality.core import app
from portality.models import Account


def api_key_required(fn):
    """ Decorator for API functions, requiring a valid key to find a user """
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        api_key = request.values.get("api_key", None)
        if api_key is not None:
            user = Account.pull_by_api_key(api_key)
            if user is not None:
                if login_user(user, remember=False):
                    return fn(*args, **kwargs)
        # else
        raise Api401Error("An API Key is required to access this.")

    return decorated_view


def api_key_optional(fn):
    """ Decorator for API functions, requiring a valid key to find a user if a key is provided. OK if none provided. """
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        api_key = request.values.get("api_key", None)
        if api_key:
            user = Account.pull_by_api_key(api_key)
            if user is not None:
                if login_user(user, remember=False):
                    return fn(*args, **kwargs)
            # else
            abort(401)

        # no api key, which is ok
        return fn(*args, **kwargs)

    return decorated_view


def ssl_required(fn):
    """ Decorator for when a view f() should be served only over SSL """
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        if app.config.get("SSL"):
            if request.is_secure:
                return fn(*args, **kwargs)
            else:
                return redirect(request.url.replace("http://", "https://"))

        return fn(*args, **kwargs)

    return decorated_view


def restrict_to_role(role):
    if current_user.is_anonymous():
        flash('You are trying to access a protected area. Please log in first.', 'error')
        return redirect(url_for('account.login', next=request.url))

    if not current_user.has_role(role):
        flash('You do not have permission to access this area of the site.', 'error')
        return redirect(url_for('doaj.home'))


def write_required(fn):
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        if app.config.get("READ_ONLY_MODE", False):
            return render_template("doaj/readonly.html")

        return fn(*args, **kwargs)

    return decorated_view
