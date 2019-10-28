from portality.lib import dates

class QueryBuilder(object):
    def __init__(self):
        self.fields = []

    def add_string_field(self, field, value, fuzzy=False):
        self.fields.append((field, value, fuzzy))

    def add_date_field(self, field, fro, to=None):
        value = fro
        if to is not None:
            value = "[" + fro + " TO " + to + "]"
        self.fields.append((field, value, True))

    def to_url_query_param(self):
        q = ""
        for field, value, fuzzy in self.fields:
            wrap = "\"" if not fuzzy else ""
            if q != "":
                q += " "
            q += field + ":" + wrap + value + wrap
        return q

####################################################
## Some utility functions which will return potted
## queries for common things you might want to know

def oa_issn_updated(issn, fro, to=None, date_sort=False):
    """
    Query by ISSN for articles in the OA subset which have been
    updated between the supplied dates

    :param issn: ISSN of the journal
    :param fro: updated since (YYYY-MM-DD)
    :param to: updated before (YYYY-MM-DD)
    :return:
    """

    fro = dates.reformat(fro, out_format="%Y-%m-%d")
    if to is not None:
        to = dates.reformat(to, out_format="%Y-%m-%d")

    qb = QueryBuilder()
    qb.add_string_field("ISSN", issn)
    qb.add_string_field("OPEN_ACCESS", "y")
    qb.add_date_field("UPDATE_DATE", fro, to)
    if date_sort:
        qb.add_string_field("sort_date", "y")
    return qb
