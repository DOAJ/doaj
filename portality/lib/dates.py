from portality.core import app

from datetime import datetime

def parse(s, format=None, guess=True):
    s = s.strip()

    if format is not None:
        try:
            return datetime.strptime(s, format)
        except ValueError as e:
            if not guess:
                raise e

    for f in app.config.get("DATE_FORMATS", []):
        try:
            return datetime.strptime(s, f)
        except ValueError as e:
            pass

    raise ValueError("Unable to parse {x} with any known format".format(x=s))

def format(d, format=None):
    if format is None:
        format = app.config.get("DEFAULT_DATE_FORMAT")
    return unicode(d.strftime(format))

def reformat(s, in_format=None, out_format=None):
    return format(parse(s, format=in_format), format=out_format)

def now():
    return format(datetime.utcnow())