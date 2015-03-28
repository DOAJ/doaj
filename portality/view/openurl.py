import re
from flask import Blueprint, request, redirect, url_for
from portality.models import OpenURLRequest
from urllib import unquote

blueprint = Blueprint('openurl', __name__)

@blueprint.route("/openurl", methods=["GET", "POST"])
def openurl():

    # Drop the first part of the url to get the raw query
    url_query = request.url.split(request.base_url).pop()

    # Validate the query syntax version and build an object representing it
    parsed_object = parse_query(url_query)

    # If it's not parsed to an OpenURLRequest, it's a redirect URL to try again.
    if type(parsed_object) != OpenURLRequest:
        return redirect(parsed_object, 301)

    # Issue query and redirect to results page
    results = parsed_object.query_es()
    results_url = get_result_page(results)
    return redirect(results_url)

def parse_query(url_query_string):
    """
    Create the model which holds the query
    :param url_query_string: The query part of an incoming OpenURL request
    :return: an object representing the query
    """
    # Check if this is new or old syntax, translate if necessary
    match_1_0 = re.compile("url_ver=Z39.88-2004")
    if not match_1_0.search(url_query_string):
        print "Legacy OpenURL 0.1 request: " + unquote(request.url)
        return old_to_new()

    print "OpenURL 1.0 request: " + unquote(request.url)

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

def old_to_new():
    """
    Translate the OpenURL 0.1 syntax to 1.0, to provide a redirect.
    :param url_query_string: An incoming OpenURL request
    :return: An OpenURL 1.0 query string
    """

    # The meta parameters in the preamble.
    params = {'url_ver': 'Z39.88-2004', 'url_ctx_fmt': 'info:ofi/fmt:kev:mtx:ctx','rft_val_fmt': 'info:ofi/fmt:kev:mtx:journal'}

    # In OpenURL 0.1, jtitle is just title. This function substitutes them.
    sub_title = lambda x: re.sub('^title', 'jtitle', x)

    # Add referrent tags to each parameter, and change title tag using above function
    rewritten_params = {"rft." + sub_title(key): value for (key, value) in request.values.iteritems()}

    # Add the rewritten parameters to the meta params
    params.update(rewritten_params)

    redirect_url = url_for('.openurl', **params)
    return redirect_url

def get_result_page(results):
    if results['hits']['total'] > 0:
        if results['hits']['hits'][0]['_type'] == 'journal':
            return url_for("doaj.toc", identifier=results['hits']['hits'][0]['_id'])
        elif results['hits']['hits'][0]['_type'] == 'article':
            return url_for("doaj.article_page", identifier=results['hits']['hits'][0]['_id'])
    else:
        # No results found for query
        pass
