from flask import Blueprint, request
from portality.models import OpenURLRequest

blueprint = Blueprint('openurl', __name__)

@blueprint.route("/openurl", methods=["GET", "POST"])
def openurl():

    # Drop the first part of the url to get the raw query
    url_query = request.url.split(request.base_url).pop()

    # Parse the query to get an object representing it
    query_object = parse_query(url_query)
    print query_object

    return url_query

def parse_query(url_query_string):
    """
    Create the model which holds the query
    :param url_query_string: The query part of an incoming OpenURL request
    :return: an object representing the query
    """

    # Split the parameter string into its constituents; pop the first item (which should just be schema specifications)
    list_of_params = url_query_string.split("&rft.") or []
    openurl_preamble = list_of_params.pop(0) or ""              #FIXME: if preamble is omitted in request, this may remove useful info

    # Pack the list of parameters into a dictionary
    dict_params = {key: value for [key, value] in map(lambda x: x.split('='), list_of_params)}

    # Create an object to represent this OpenURL request.
    try:
        query_object = OpenURLRequest(**dict_params)
    except:
        query_object = None
        print "Failed to create OpenURLRequest object"

    return query_object

def old_to_new(url_query_string):
    """
    Translate the OpenURL 0.1 syntax to 1.0, to provide a redirect.
    :param url_query_string: An incoming OpenURL request
    :return: An OpenURL 1.0 query string
    """


