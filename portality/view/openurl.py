from flask import Blueprint, request

blueprint = Blueprint('openurl', __name__)

@blueprint.route("/openurl", methods=["GET", "POST"])
def openurl():

    # Drop the first part of the url to get the raw query
    url_query = request.url.split(request.base_url).pop()
    return url_query

def parse_query(url_query_string):
    """
    Create the model which holds the query
    :param url_query_string: An incoming OpenURL request
    :return: an object representing the query
    """
    return url_query_string

def old_to_new(url_query_string):
    """
    Translate the OpenURL 0.1 syntax to 1.0, to provide a redirect.
    :param url_query_string: An incoming OpenURL request
    :return: An OpenURL 1.0 query string
    """


