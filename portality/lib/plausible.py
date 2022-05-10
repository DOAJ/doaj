""" Plausible Analytics
"""
import json
import logging
import os
from functools import wraps
from threading import Thread

import requests

from portality.core import app

logger = logging.getLogger(__name__)


def create_logfile(log_dir=None):
    filepath = __name__ + '.log'
    if log_dir is not None:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        filepath = os.path.join(log_dir, filepath)
        fh = logging.FileHandler(filepath)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(fh)


def send_event(goal: str, on_completed=None, **props_kwargs):
    """ Send event data to Plausible Analytics. (ref: https://plausible.io/docs/events-api )
    """

    host_url = app.config.get('PLAUSIBLE_URL', '')
    if host_url:
        logger.warning('skip send_event, PLAUSIBLE_URL undefined')
        return

    # prepare request payload
    payload = {'name': goal,
               'url': app.config.get('BASE_URL', 'http://localhost'),
               'domain': app.config.get('PLAUSIBLE_SITE_NAME', 'localhost'), }
    if props_kwargs:
        payload['props'] = json.dumps(props_kwargs)

    def _send():
        resp = requests.post(f'{host_url}/api/event/', json=payload,
                             proxies={
                                 'http': 'http://localhost:58484',
                                 'https': 'http://localhost:58484',
                             })
        if on_completed:
            if resp.status_code >= 300:
                logger.warning(f'send plausible event api fail. [{resp.status_code}][{resp.text}]')

            on_completed(resp)

    Thread(target=_send).start()


def pa_event(goal, action, label='',
             record_value_of_which_arg='', **prop_kwargs):
    """
    Decorator for Flask view functions, sending event data to Plausible
    Analytics.
    """

    def decorator(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            # define event label
            el = label
            if record_value_of_which_arg in kwargs:
                el = kwargs[record_value_of_which_arg]

            # prepare event props payload
            event_payload = {
                'action': action,
                'label': el,
            }
            if prop_kwargs:
                event_payload.update(prop_kwargs)

            # send event
            send_event(goal, **event_payload)

            return fn(*args, **kwargs)

        return decorated_view

    return decorator
