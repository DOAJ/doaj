# ~~Coerce:Library~~
from portality.lib import dates, val_convert
from datetime import date, datetime
from portality.lib import seamless
from portality.datasets import get_country_code, get_currency_code


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


def to_currency_code(val):
    """
    ~~-> Currencies:Data~~
    :param val:
    :return:
    """
    if val is None:
        return None
    nv = get_currency_code(val)
    if nv is None:
        raise ValueError("Unable to convert {x} to a valid currency code".format(x=val))
    uc = seamless.to_utf8_unicode
    return uc(nv)



def to_issn(issn):
    if len(issn) > 9 or issn == '':
        raise ValueError("Unable to normalise {x} to valid ISSN".format(x=issn))

    issn = issn.upper()
    if len(issn) == 9:
        return issn

    if len(issn) == 8:
        if "-" in issn:
            return "0" + issn
        else:
            return issn[:4] + "-" + issn[4:]

    if len(issn) < 8:
        if "-" in issn:
            return ("0" * (9 - len(issn))) + issn
        else:
            issn = ("0" * (8 - len(issn))) + issn
            return issn[:4] + "-" + issn[4:]


# ~~-> Seamless:Library~~
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
    "utcdatetimemicros" : date_str(out_format="%Y-%m-%dT%H:%M:%S.%fZ"),
    "bigenddate" : date_str(out_format="%Y-%m-%d"),
    "isolang": val_convert.create_fn_to_isolang( is_upper=True),
    "isolang_2letter": val_convert.create_fn_to_isolang(output_format="alpha2", is_upper=True),
    "country_code": val_convert.to_country_code_3,
    "currency_code": to_currency_code,
    "issn" : to_issn
}