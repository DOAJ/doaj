from portality.lib import dates

def to_datestamp(in_format=None):
    def stampify(val):
        return dates.parse(val, format=in_format)
    return stampify