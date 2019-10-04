#import UniversalAnalytics
#from pyga.requests import Tracker
import logging
import os
from functools import wraps

# Logger specific to analytics
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# The global tracker object
tracker = None


class GAException(Exception):
    pass


def create_tracker(ga_id, domain):
    global tracker
    if ga_id:
        # fixme: tracker is broken for now because universal-analytics is not python3 compatible
        #tracker = UniversalAnalytics.Tracker.create(ga_id, client_id=domain)
        #tracker = Tracker(ga_id, domain)
        raise GAException("GA is not running because universal-analytics is broken")
    else:
        raise GAException("Invalid GA ID supplied, no tracker created.")


def create_logfile(log_dir=None):
    filepath = __name__ + '.log'
    if log_dir is not None:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        filepath = os.path.join(log_dir, filepath)
        fh = logging.FileHandler(filepath)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(fh)


class GAEvent(object):
    category = None
    action = None
    label = None
    value = None
    fieldsobject = None

    def __init__(self, category, action, label='', value=None, fieldsobject=None):
        self.category = category
        self.action = action
        self.label = label
        self.value = value
        self.fieldsobject=fieldsobject

    def submit(self):
        ga_send_event(self.category, self.action, self.label, self.value, self.fieldsobject)


def ga_send_event(category, action, label='', value=None, fieldsobject=None):
    """
    Send event data to Google Analytics.
    (supposedly supporting other analytics providers as well,
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

    :param category: Typically the object that was interacted with (e.g. 'Video')
    :param action: The type of interaction (e.g. 'play')
    :param label: Useful for categorizing events (e.g. 'Fall Campaign')
    :param value: A non-negative numeric value associated with the event (e.g. 42)
    :param fieldsobject: Key, value pairs which don't fit into the above categories
    """

    if tracker is not None:
        analytics_args = [category, action]

        if label != '':
            analytics_args.append(label)

        if value is not None:
            analytics_args.append(value)

        if fieldsobject is not None:
            analytics_args.append(fieldsobject)

        logger.debug("Event Send %s", analytics_args)
        tracker.send('event', *analytics_args)
    else:
        logger.error("Google Analytics tracker is not configured.")


def sends_ga_event(event_category, event_action, event_label='',
                   event_value=0, record_value_of_which_arg=''):
    """
    Decorator for Flask view functions, sending event data to Google
    Analytics.

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
        @sends_ga_event('API Hit', 'Search applications',
                         record_value_of_which_arg='search_query')
        def search_applications(search_query):
            # ...

    Then we get a hit, with search_query being set to 'computer shadows'.
    This will result in an event with category "API Hit", action "Search
    applications" and label "computer shadows".

    A different example:
        @sends_ga_event('API Hit', 'Retrieve application',
                         record_value_of_which_arg='application_id')
        def retrieve_application(application_id):
            # ...

    Then we get a hit asking for application with id '12345'.
    This will result in an event with category "API Hit", action "Retrieve
    application" and label "12345".

    Clashing arguments:
        @sends_ga_event('API Hit', 'Retrieve application',
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

    def decorator(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            el = event_label
            if record_value_of_which_arg in kwargs:
                el = kwargs[record_value_of_which_arg]

            ga_send_event(event_category, event_action, el, event_value)

            return fn(*args, **kwargs)

        return decorated_view
    return decorator
