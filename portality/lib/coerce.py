from portality.lib import dates
from datetime import date, datetime
from portality.lib import seamless

def to_datestamp(in_format=None):
    def stampify(val):
        return dates.parse(val, format=in_format)
    return stampify

def date_str(in_format=None, out_format=None):
    def datify(val):
        if val is None or val == "":
            return None
        if isinstance(val, date) or isinstance(val, datetime):
            return dates.format(val, format=out_format)
        else:
            return dates.reformat(val, in_format=in_format, out_format=out_format)

    return datify

COERCE_MAP = {
    "unicode": seamless.to_utf8_unicode,
    "unicode_upper" : seamless.to_unicode_upper,
    "unicode_lower" : seamless.to_unicode_lower,
    "integer": seamless.intify,
    "float": seamless.floatify,
    "url": seamless.to_url,
    "bool": seamless.to_bool,
    "datetime" : seamless.to_datetime,
    "utcdatetime" : date_str(),
    "bigenddate" : date_str(out_format="%Y-%m-%d")
}