from portality.core import app

from datetime import datetime, timedelta
from random import randint

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

def random_date(fro=None, to=None):
    if fro is None:
        fro = parse("1970-01-01T00:00:00Z")
    if isinstance(fro, basestring):
        fro = parse(fro)
    if to is None:
        to = datetime.utcnow()
    if isinstance(to, basestring):
        to = parse(to)

    span = int((to - fro).total_seconds())
    s = randint(0, span)
    return format(to - timedelta(seconds=s))