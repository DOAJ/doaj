"""Deals with encoding, decoding and modifying Elasticsearch queries in an HTTP environment, e.g. in URLs, in POST data, in JSON, etc."""

from copy import deepcopy


def remove_fields(query, fields_to_remove):
    q = deepcopy(query)
    for del_attr in fields_to_remove:
        if del_attr in q:
            del q[del_attr]
    return q


def remove_search_limits(query):
    return remove_fields(query, ['size', 'from'])
