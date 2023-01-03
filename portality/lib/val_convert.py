from typing import Callable, Any


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
