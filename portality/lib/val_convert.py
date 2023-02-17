"""
contain functions or factory which provide value conversion(coerce) in
SeamlessMixin or DataObj layer
"""

from typing import Callable, Any

from portality.datasets import get_country_code_3


def create_fn_to_isolang(output_format=None, is_upper=False) -> Callable[[Any], str]:
    """
    :param is_upper: return upper code if True
    :param output_format: format from input source to putput.  Must be one of:
        * alpha3
        * alt3
        * alpha2
        * name
        * fr
    Can be a list in order of preference, too
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
        if l is None:
            raise ValueError("Unable to find iso code for language {x}".format(x=val))
        for f in output_format:
            v = l.get(f)
            if v is None or v == "":
                continue
            return v.upper() if is_upper else v

    return isolang


def to_utf8_unicode(val) -> str:
    if isinstance(val, str):
        return val
    elif isinstance(val, str):  # why check isinstance(val, str) again ??
        try:
            return val.decode("utf8", "strict")
        except UnicodeDecodeError:
            raise ValueError("Could not decode string")
    else:
        return str(val)


def to_country_code_3(val):
    """
    ~~-> Countries:Data~~
    :param val:
    :return:
    """
    if val is None:
        return None
    nv = get_country_code_3(val, fail_if_not_found=True)
    if nv is None:
        raise ValueError("Unable to convert {x} to a valid country code".format(x=val))
    uc = to_utf8_unicode
    return uc(nv)
