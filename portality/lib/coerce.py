# ~~Coerce:Library~~
from portality.lib import dates
from datetime import date, datetime
from portality.lib import seamless
from portality.datasets import get_country_code, get_currency_code
from portality.lib.dates import FMT_DATETIME_MS_STD, FMT_DATE_STD


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

def find_earliest_date(dates_arr, dates_format, out_format=None):
    parsed_dates = [dates.parse(date, dates_format) for date in dates_arr]
    earliest_date = min(parsed_dates)
    result = dates.format(earliest_date, out_format or dates_format)
    print(result)
    return dates.format(earliest_date, out_format or dates_format)


def to_isolang(output_format=None, fail_if_not_found=True):
    """
    :param output_format: format from input source to putput.  Must be one of:
        * alpha3
        * alt3
        * alpha2
        * name
        * fr
    Can be a list in order of preference, too
    :param fail_if_not_found: Whether to raise ValueError if there's no match or return the input unchanged
    ~~-> Languages:Data~~
    :return:
    """
    # delayed import, since we may not always want to load the whole dataset for a dataobj
    from portality.lib import isolang as dataset

    # sort out the output format list
    if output_format is None:
        output_format = ["alpha3"]
    if not isinstance(output_format, list):
        output_format = [output_format]

    def isolang(val):
        if val is None:
            return None
        l = dataset.find(val)

        # If we didn't find the language, either raise an error or return the provided value
        if l is None:
            if fail_if_not_found is True:
                raise ValueError("Unable to find iso code for language {x}".format(x=val))
            else:
                return val

        # Retrieve the correct output format from a successful match
        for f in output_format:
            v = l.get(f)
            if v is None or v == "":
                continue
            return v.upper()

    return isolang


def to_currency_code(fail_if_not_found=True):
    """
    ~~-> Currencies:Data~~
    :param val:
    :param fail_if_not_found:
    :return:
    """

    def codify(val):
        if val is None:
            return None
        nv = get_currency_code(val, fail_if_not_found=fail_if_not_found)
        if nv is None:
            raise ValueError("Unable to convert {x} to a valid currency code".format(x=val))
        uc = seamless.to_utf8_unicode
        return uc(nv)

    return codify


def to_country_code(val):
    """
    ~~-> Countries:Data~~
    :param val:
    :return:
    """
    if val is None:
        return None
    nv = get_country_code(val, fail_if_not_found=True)
    if nv is None:
        raise ValueError("Unable to convert {x} to a valid country code".format(x=val))
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
    "unicode_upper": seamless.to_unicode_upper,
    "unicode_lower": seamless.to_unicode_lower,
    "integer": seamless.intify,
    "float": seamless.floatify,
    "url": seamless.to_url,
    "bool": seamless.to_bool,
    "datetime": seamless.to_datetime,
    "utcdatetime": date_str(),
    "utcdatetimemicros": date_str(out_format=FMT_DATETIME_MS_STD),
    "bigenddate": date_str(out_format=FMT_DATE_STD),
    "isolang": to_isolang(),
    "isolang_2letter_strict": to_isolang(output_format="alpha2", fail_if_not_found=True),
    "isolang_2letter_lax": to_isolang(output_format="alpha2", fail_if_not_found=False),
    "country_code": to_country_code,
    "issn": to_issn,
    "currency_code_strict": to_currency_code(fail_if_not_found=True),
    "currency_code_lax": to_currency_code(fail_if_not_found=False)
}
