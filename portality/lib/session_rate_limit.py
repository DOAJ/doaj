from functools import wraps
from flask import session, abort, request
import time
from itertools import izip, cycle
from portality.core import app

def set_session_var(var_name):

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.has_key("qa"):
                sv = _xor_crypt_string("initialised", app.config.get("SECRET_KEY"))
                session[var_name] = sv
            return f(*args, **kwargs)
        return decorated_function

    return decorator


def rate_limit(var_name, bypass_field=None, bypass_val=None):

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if bypass_field is not None and bypass_val is not None:
                val = request.values.get(bypass_field)
                if val is not None and val == bypass_val:
                    return f(*args, **kwargs)

            if not session.has_key(var_name):
                abort(400)
            ts = _xor_crypt_string(session[var_name], app.config.get("SECRET_KEY"))
            if ts == "initialised":
                ts = 0
            ts = float(ts)
            now = time.time()
            td = now - ts
            if td < 0.5:    # 2 requests per second
                abort(429)
            sv = _xor_crypt_string(str(now), app.config.get("SECRET_KEY"))
            session[var_name] = sv

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def _xor_crypt_string(data, key):
    return ''.join(chr(ord(x) ^ ord(y)) for (x,y) in izip(data, cycle(key)))