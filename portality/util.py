from urllib.request import urlopen
from urllib.parse import urlencode
import md5
import re, string
from unicodedata import normalize
from functools import wraps
from flask import request, current_app, flash, make_response
from random import choice
import json

from urllib.parse import urlparse, urljoin


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    if ( test_url.scheme in ('http', 'https') and 
            ref_url.netloc == test_url.netloc ):
        return target
    else:
        return '/'


def jsonp(f):
    """Wraps JSONified output for JSONP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f(*args,**kwargs).data) + ')'
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
        

# derived from http://flask.pocoo.org/snippets/5/ (public domain)
# changed delimiter to _ instead of - due to ES search problem on the -
_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
def slugify(text, delim='_'):
    """Generates an slightly worse ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', word).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return str(delim.join(result))


# get gravatar for email address
def get_gravatar(email, size=None, default=None, border=None):
    email = email.lower().strip()
    hash = md5.md5(email).hexdigest()
    args = {'gravatar_id':hash}
    if size and 1 <= int(size) <= 512:
        args['size'] = size
    if default: args['default'] = default
    if border: args['border'] = border

    url = 'http://www.gravatar.com/avatar.php?' + urlencode(args)

    response = urlopen(url)
    image = response.read()
    response.close()

    return image


def generate_password(length=8):
    chars = string.letters + string.digits
    pw = ''.join(choice(chars) for _ in range(length))
    return pw


def flash_with_url(message, category=''):
    flash(message, category + '+contains-url')


def listpop(l, default=None):
    return l[0] if l else default


def parse_date(s, format=None, guess=True):
    s = s.strip()

    if format is not None:
        try:
            return datetime.strptime(s, format)
        except ValueError as e:
            if not guess:
                raise e

    for f in current_app.config.get("DATE_FORMATS", []):
        try:
            return datetime.strptime(s, f)
        except ValueError as e:
            pass

    raise ValueError("Unable to parse {x} with any known format".format(x=s))


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
    with open(filename, 'rb') as f:
        content = f.read()
    return content


def unicode_dict(d):
    """ Recursively convert dictionary keys to unicode """
    if isinstance(d, dict):
        return dict((str(k), unicode_dict(v)) for k, v in list(d.items()))
    elif isinstance(d, list):
        return [unicode_dict(e) for e in d]
    else:
        return d


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
