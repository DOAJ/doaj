import json
from functools import wraps
from flask import request, abort, redirect, flash, url_for, render_template, make_response
from flask_login import login_user, current_user

from portality.api.v1.common import Api401Error

from portality.core import app
from portality.models import Account


def swag(swag_summary, swag_spec):
    """ Decorator for API functions, adding swagger info to the swagger spec."""
    def decorator(f):
        f.summary = swag_summary
        f.swag = swag_spec
        return f

    return decorator


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
    if current_user.is_anonymous:
        flash('You are trying to access a protected area. Please log in first.', 'error')
        return redirect(url_for('account.login', next=request.url))

    if not current_user.has_role(role):
        flash('You do not have permission to access this area of the site.', 'error')
        return redirect(url_for('doaj.home'))


def write_required(script=False, api=False):
    def decorator(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if app.config.get("READ_ONLY_MODE", False):
                # TODO remove "script" argument from decorator.
                # Should be possible to detect if this is run in a web context or not.
                if script:
                    raise RuntimeError('This task cannot run since the system is in read-only mode.')
                elif api:
                    resp = make_response(json.dumps({"message" : "We are currently carrying out essential maintenance, and this route is temporarily unavailable"}), 503)
                    resp.mimetype = "application/json"
                    return resp
                else:
                    return render_template("doaj/readonly.html")

            return fn(*args, **kwargs)

        return decorated_view
    return decorator
