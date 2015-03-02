import re
from urllib import unquote
from flask import Blueprint, request
from portality.models import OpenURLRequest

blueprint = Blueprint('openurl', __name__)

@blueprint.route("/openurl", methods=["GET", "POST"])
def openurl():

    # Drop the first part of the url to get the raw query
    url_query = request.url.split(request.base_url).pop()

    # Validate the query syntax version and build an object representing it
    query_object = parse_query(url_query)

    return str(query_object)

def parse_query(url_query_string):
    """
    Create the model which holds the query
    :param url_query_string: The query part of an incoming OpenURL request
    :return: an object representing the query
    """
    # Check if this is new or old syntax, translate if necessary
    match_1_0 = re.compile("url_ver=Z39.88-2004")
    if not match_1_0.search(url_query_string):
        old_to_new(url_query_string)

    # Wee function to strip of the referrant namespace prefix from paramaterss
    rem_ns = lambda x: re.sub('rft.', '', x)

    # Pack the list of parameters into a dictionary, while un-escaping the string.
    dict_params = {rem_ns(key): value for (key, value) in request.values.iteritems()}

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
    print "old_to_new"
    return url_query_string


