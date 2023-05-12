# ~~ Dates:Library~~

import math
from datetime import datetime, timedelta
from random import randint

# Extracted from settings.py to prevent circular import
config = {
    # when dates.format is called without a format argument, what format to use?
    'DEFAULT_DATE_FORMAT': "%Y-%m-%dT%H:%M:%SZ",

    # date formats that we know about, and should try, in order, when parsing
    'DATE_FORMATS': [
        "%Y-%m-%dT%H:%M:%S.%fZ",   # e.g. 2010-01-01T00:00:00.000Z
        "%Y-%m-%dT%H:%M:%SZ",   # e.g. 2014-09-23T11:30:45Z
        "%Y-%m-%d",             # e.g. 2014-09-23
        "%d/%m/%y",             # e.g. 29/02/80
        "%d/%m/%Y",             # e.g. 29/02/1980
        "%d-%m-%Y",             # e.g. 01-01-2015
        "%Y.%m.%d",             # e.g. 2014.09.12
        "%d.%m.%Y",             # e.g. 12.9.2014
        "%d.%m.%y",             # e.g. 12.9.14
        "%d %B %Y",             # e.g. 21 June 2014
        "%d-%b-%Y",             # e.g. 31-Jul-13
        "%d-%b-%y",             # e.g. 31-Jul-2013
        "%b-%y",                # e.g. Aug-13
        "%B %Y",                # e.g. February 2014
        "%Y"                    # e.g. 1978
    ],

    # The last_manual_update field was initialised to this value. Used to label as 'never'.
    'DEFAULT_TIMESTAMP': "1970-01-01T00:00:00Z",
}


FMT_DATETIME_STD = config.get('DEFAULT_DATE_FORMAT', '%Y-%m-%dT%H:%M:%SZ')
FMT_DATETIME_A = '%Y-%m-%d %H:%M:%S'
FMT_DATETIME_MS_STD = '%Y-%m-%dT%H:%M:%S.%fZ'
FMT_DATETIME_SHORT = '%Y%m%d_%H%M'

FMT_DATE_STD = '%Y-%m-%d'
FMT_DATE_SHORT = '%Y%m%d'
FMT_DATE_DOT = '%Y.%m.%d'
FMT_DATE_HUMAN = '%d %B %Y'
FMT_DATE_HUMAN_A = '%d/%b/%Y'
FMT_DATE_YM = '%Y-%m'
FMT_DATE_YMDOT = '%Y.%m'

FMT_TIME_SHORT = '%H%M'
FMT_YEAR = '%Y'

DEFAULT_TIMESTAMP_VAL = config.get('DEFAULT_TIMESTAMP', '1970-01-01T00:00:00Z')


def parse(s, format=None, guess=True) -> datetime:
    s = s.strip()

    if format is not None:
        try:
            return datetime.strptime(s, format)
        except ValueError as e:
            if not guess:
                raise e

    for f in config.get("DATE_FORMATS", []):
        try:
            return datetime.strptime(s, f)
        except ValueError as e:
            pass

    raise ValueError("Unable to parse {x} with any known format".format(x=s))


def format(d, format=None) -> str:
    return d.strftime(format or FMT_DATETIME_STD)


def reformat(s, in_format=None, out_format=None) -> str:
    return format(parse(s, format=in_format), format=out_format)


def now() -> datetime:
    """ standard now function for DOAJ  """
    return datetime.utcnow()


def now_str(fmt=FMT_DATETIME_STD) -> str:
    return format(now(), format=fmt)


def now_str_with_microseconds() -> str:
    return format(now(), format=FMT_DATETIME_MS_STD)


def today() -> str:
    return format(now(), format=FMT_DATE_STD)


def random_date(fro: datetime = None, to: datetime = None) -> str:
    if fro is None:
        fro = parse(DEFAULT_TIMESTAMP_VAL)
    if isinstance(fro, str):
        fro = parse(fro)
    if to is None:
        to = now()
    if isinstance(to, str):
        to = parse(to)

    span = int((to - fro).total_seconds())
    s = randint(0, span)
    return format(to - timedelta(seconds=s))


def before(timestamp, seconds) -> datetime:
    return timestamp - timedelta(seconds=seconds)


def before_now(seconds: int) -> datetime:
    return before(now(), seconds)


def after(timestamp, seconds) -> datetime:
    return timestamp + timedelta(seconds=seconds)


def eta(since, sofar, total) -> str:
    td = (now() - since).total_seconds()
    spr = float(td) / float(sofar)
    alltime = int(math.ceil(total * spr))
    fin = after(since, alltime)
    return format(fin)


def day_ranges(fro: datetime, to: datetime) -> 'list[str]':
    aday = timedelta(days=1)

    # first, workout when the next midnight point is
    next_day = fro + aday
    next_midnight = datetime(next_day.year, next_day.month, next_day.day)

    # in the degenerate case, to is before the next midnight, in which case they both
    # fall within the one day range
    if next_midnight > to:
        return [(format(fro), format(to))]

    # start the range off with the remainder of the first day
    ranges = [(format(fro), format(next_midnight))]

    # go through each day, adding to the range, until the next day is after
    # the "to" date, then finish up and return
    current = next_midnight
    while True:
        next = current + aday
        if next > to:
            ranges.append((format(current), format(to)))
            break
        else:
            ranges.append((format(current), format(next)))
            current = next

    return ranges


def human_date(stamp, string_format=FMT_DATE_HUMAN) -> str:
    return reformat(stamp, out_format=string_format)
