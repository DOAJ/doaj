import json
from functools import wraps
from flask import request, current_app, flash, make_response
from urllib.parse import urlparse, urljoin


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
        payload = json.loads(request.data)
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
