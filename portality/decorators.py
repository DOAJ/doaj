import json, signal, datetime
from functools import wraps
from flask import request, abort, redirect, flash, url_for, render_template, make_response
from flask_login import login_user, current_user

from portality.api.v1.common import Api401Error

from portality.core import app
from portality.models import Account
from portality.models.harvester import HarvesterProgressReport as Report


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


class CaughtTermException(Exception):
    pass


def _term_handler(signum, frame):
    app.logger.warning("Harvester terminated with signal " + str(signum))
    raise CaughtTermException


def capture_sigterm(fn):
    # Register the SIGTERM handler to raise an exception, allowing graceful exit.
    signal.signal(signal.SIGTERM, _term_handler)

    """ Decorator which allows graceful exit on SIGTERM """
    @wraps(fn)
    def decorated_fn(*args, **kwargs):
        try:
            fn(*args, **kwargs)
        except (CaughtTermException, KeyboardInterrupt):
            app.logger.warning(u"Harvester caught SIGTERM. Exiting.")
            report = Report.write_report()
            if app.config.get("EMAIL_ON_EVENT", False):
                to = app.config.get("EMAIL_RECIPIENTS", None)
                fro = app.config.get("SYSTEM_EMAIL_FROM")

                if to is not None:
                    from portality import app_email as mail
                    mail.send_mail(
                        to=app.config["EMAIL_RECIPIENTS"],
                        fro=fro,
                        subject="DOAJ Harvester caught SIGTERM at {0}".format(
                            datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")),
                        msg_body=report
                    )
            app.logger.info(report)
            exit(1)

    return decorated_fn