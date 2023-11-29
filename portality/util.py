import json
import urllib.request
from functools import wraps

import werkzeug.routing
from flask import request, current_app, flash, make_response, url_for as flask_url_for
from urllib.parse import urlparse, urljoin
from portality.core import app


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    if test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc:
        return target
    else:
        return '/'


def jsonp(f):
    """Wraps JSONified output for JSONP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f(*args, **kwargs).data.decode("utf-8")) + ')'
            return current_app.response_class(content, mimetype='application/javascript')
        else:
            return f(*args, **kwargs)
    return decorated_function


# derived from http://flask.pocoo.org/snippets/45/ (pd) and customised
def request_wants_json():
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    if best == 'application/json' and request.accept_mimetypes[best] > request.accept_mimetypes['text/html']:
        best = True
    else:
        best = False
    if request.values.get('format','').lower() == 'json' or request.path.endswith(".json"):
        best = True
    return best


def flash_with_url(message, category=''):
    flash(message, category + '+contains-url')


def listpop(l, default=None):
    return l[0] if l else default


def normalise_issn(issn):
    issn = issn.upper()
    if len(issn) > 8:
        return issn
    if len(issn) == 8:
        if "-" in issn:
            return "0" + issn
        else: return issn[:4] + "-" + issn[4:]
    if len(issn) < 8:
        if "-" in issn:
            return ("0" * (9 - len(issn))) + issn
        else:
            issn = ("0" * (8 - len(issn))) + issn
            return issn[:4] + "-" + issn[4:]


def load_file(filename):
    with open(filename, 'r') as f:
        content = f.read()
    return content


def make_json_resp(data, status_code, json_dumps_kwargs=None):
    if json_dumps_kwargs is None:
        json_dumps_kwargs = {}
    resp = make_response(json.dumps(data, **json_dumps_kwargs))
    resp.status_code = status_code
    resp.mimetype = "application/json"
    return resp


def get_web_json_payload():
    """
    Attempts to load JSON from request.data.

    If valid, returns the decoded JSON payload to the caller.
    If invalid returns a JSON response with a 400 Bad Request to the web user.
    """
    r = {}
    try:
        payload = json.loads(request.data.decode("utf-8"))
    except ValueError:
        r['error'] = "Invalid JSON payload from request.data .\n{}".format(request.data)
        return make_json_resp(r, status_code=400)
    return payload


def validate_json(payload, fields_must_be_present=None, fields_must_not_be_present=None, error_to_raise=None):
    if not fields_must_be_present:
        fields_must_be_present = []

    if not fields_must_not_be_present:
        fields_must_not_be_present = []

    for f in fields_must_be_present:
        if f not in payload:
            if error_to_raise:
                raise error_to_raise('Invalid JSON. The field {} was missing and is required.'.format(f))
            else:
                return False

    for f in fields_must_not_be_present:
        if f in payload:
            if error_to_raise:
                raise error_to_raise('Invalid JSON. The field {} was present and must not be present.'.format(f))
            else:
                return False

    return True


def batch_up(long_list, batch_size):
    """Yield successive n-sized chunks from l (a list)."""
    # http://stackoverflow.com/a/312464/1154882
    for i in range(0, len(long_list), batch_size):
        yield long_list[i:i + batch_size]


def ipt_prefix(type):
    """ For IPT connections, prepend the index prefix to the type so we connect to the right index-per-type index. """
    # ~~Elasticsearch:Technology~~
    if app.config['ELASTIC_SEARCH_INDEX_PER_TYPE']:
        return app.config['ELASTIC_SEARCH_DB_PREFIX'] + type
    else:
        return type


def verify_recaptcha(g_recaptcha_response):
    """
    ~~ReCAPTCHA:ExternalService~~
    :param g_recaptcha_response:
    :return:
    """
    with urllib.request.urlopen('https://www.recaptcha.net/recaptcha/api/siteverify?secret=' + app.config.get("RECAPTCHA_SECRET_KEY") + '&response=' + g_recaptcha_response) as url:
        data = json.loads(url.read().decode())
        return data


def url_for(*args, **kwargs):
    """
    This function is a hack to allow us to use url_for where we may nor may not have the
    right request context.

    HACK: this bit of code is required because notifications called from huey using the shortcircuit event
    dispatcher do not have the correct request context, and I was unable to figure out how to set the correct
    one in the framework above.  So instead this is a dirty workaround which pushes the right test context
    if needed.

    :param args:
    :param kwargs:
    :return:
    """
    try:
        url = flask_url_for(*args, **kwargs)
    except:
        from portality.app import app as doajapp

        with doajapp.test_request_context("/"):
            url = flask_url_for(*args, **kwargs)

    return url


def get_full_url_by_endpoint(endpoint):
    """
    werkzeug.routing.BuildError will be throw if rout endpoint not found
    """
    return app.config.get("BASE_URL", "https://doaj.org") + url_for(endpoint)


def get_full_url_safe(endpoint):
    try:
        return get_full_url_by_endpoint(endpoint)
    except werkzeug.routing.BuildError:
        app.logger.warning(f'endpoint not found -- [{endpoint}]')
        return None


def no_op(*args, **kwargs):
    """ noop (no operation) function """
    pass


def custom_timed_rotating_logger(file_name):
    """Custom Logger to log to specified file name"""
    import os
    import logging
    from logging.handlers import TimedRotatingFileHandler
    # Create a logger
    logger = logging.getLogger(os.path.splitext(file_name)[0])
    logger.setLevel(logging.DEBUG)  # Set the logging level

    # Get the user's home directory
    user_home = os.path.expanduser("~")
    log_dir = os.path.join(user_home, 'appdata', 'doaj')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_filename = os.path.join(log_dir, file_name)
    # Rotate every day. Keep 30 days worth of backup.
    handler = TimedRotatingFileHandler(log_filename, when="D", interval=1, backupCount=30)

    # Create a formatter and add it to the handler
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

    return logger
