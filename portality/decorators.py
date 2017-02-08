from functools import wraps
from flask import request, abort, redirect, flash, url_for, render_template
from flask.ext.login import current_user
from flask_login import login_user
import UniversalAnalytics

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

def track_analytics(event_category, event_action, event_label='',
                    event_value=0, record_value_of_which_arg=''):
    """
    Decorator for Flask view functions, sending event data to Google
    Analytics. (supposedly supporting other analytics providers as well,
    check https://github.com/analytics-pros/universal-analytics-python )

    See https://support.google.com/analytics/answer/1033068?hl=en for
    guidance on how to use the various event properties this decorator
    takes.

    One thing to note is that event_value must be an integer. We
    don't really use that, it's for things like "total downloads" or
    "number of times video played".

    The others are strings and can be anything we like. They must
    take into account what previous strings we've sent so that events
    can be aggregated correctly. Changing the strings you use for
    categories, actions and labels to describe the same event will
    split your analytics reports into two: before and after the
    change of the event strings you use.

    :param record_value_of_which_arg: The name of one argument that
    the view function takes. During tracking, the value of that
    argument will be extracted and sent as the Event Label to the
    analytics servers. NOTE! If you pass both event_label and
    record_value_of_which_arg to this decorator, event_label will be
    ignored and overwritten by the action that
    record_value_of_which_arg causes.

    For example:
        @track_analytics('API Hit', 'Search applications',
                         record_value_of_which_arg='search_query')
        def search_applications(search_query):
            # ...

    Then we get a hit, with search_query being set to 'computer shadows'.
    This will result in an event with category "API Hit", action "Search
    applications" and label "computer shadows".

    A different example:
        @track_analytics('API Hit', 'Retrieve application',
                         record_value_of_which_arg='application_id')
        def retrieve_application(application_id):
            # ...

    Then we get a hit asking for application with id '12345'.
    This will result in an event with category "API Hit", action "Retrieve
    application" and label "12345".

    Clashing arguments:
        @track_analytics('API Hit', 'Retrieve application',
                         event_label='Special interest action',
                         record_value_of_which_arg='application_id')
        def retrieve_application(application_id):
            # ...

    Then we get a hit asking for application with id '12345' again.
    This will result in an event with category "API Hit", action "Retrieve
    application" and label "12345". I.e. the event_label passed in will
    be ignored, because we also passed in record_value_of_which_arg which
    overrides the event label sent to the analytics servers.

    On testing: this has been tested manually on DOAJ with Google
    Analytics by @emanuil-tolev. 
    """
    ga_id = app.config.get('GOOGLE_ANALYTICS_ID', '')
    if ga_id:
        tracker = UniversalAnalytics.Tracker.create(ga_id, client_id=app.config['BASE_DOMAIN'])

    def decorator(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if ga_id:
                analytics_args = [event_category, event_action]

                final_event_label = event_label
                if record_value_of_which_arg in kwargs:
                    final_event_label = kwargs[record_value_of_which_arg]
                if final_event_label:
                    analytics_args.append(final_event_label)

                if event_value:
                    analytics_args.append(event_value)

                tracker.send('event', *analytics_args)
            return fn(*args, **kwargs)

        return decorated_view
    return decorator
