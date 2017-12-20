import UniversalAnalytics
from functools import wraps
from portality.core import app

# FIXME: A decorator isn't always the most appropriate way to send events. Sometimes we need data from within functions.


def google_analytics_event(event_category, event_action, event_label='',
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

    :param event_category:
    :param event_action:
    :param event_label:
    :param event_value:

    :param record_value_of_which_arg: The name of one argument that
    the view function takes. During tracking, the value of that
    argument will be extracted and sent as the Event Label to the
    analytics servers. NOTE! If you pass both event_label and
    record_value_of_which_arg to this decorator, event_label will be
    ignored and overwritten by the action that
    record_value_of_which_arg causes.

    For example:
        @google_analytics_event('API Hit', 'Search applications',
                         record_value_of_which_arg='search_query')
        def search_applications(search_query):
            # ...

    Then we get a hit, with search_query being set to 'computer shadows'.
    This will result in an event with category "API Hit", action "Search
    applications" and label "computer shadows".

    A different example:
        @google_analytics_event('API Hit', 'Retrieve application',
                         record_value_of_which_arg='application_id')
        def retrieve_application(application_id):
            # ...

    Then we get a hit asking for application with id '12345'.
    This will result in an event with category "API Hit", action "Retrieve
    application" and label "12345".

    Clashing arguments:
        @google_analytics_event('API Hit', 'Retrieve application',
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
    Analytics by @emanuil-tolev & @Steven-Eardley.
    """
    ga_id = app.config.get('GOOGLE_ANALYTICS_ID', '')
    if ga_id:
        tracker = UniversalAnalytics.Tracker.create(ga_id, client_id=app.config['BASE_DOMAIN'])

    def decorator(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if ga_id:
                analytics_args = [event_category, event_action]

                if record_value_of_which_arg in kwargs:
                    analytics_args.append(kwargs[record_value_of_which_arg])
                elif event_label != '':
                    analytics_args.append(event_label)

                if event_value:
                    analytics_args.append(event_value)

                tracker.send('event', *analytics_args)
            return fn(*args, **kwargs)

        return decorated_view
    return decorator
