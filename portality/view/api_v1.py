from flask import Blueprint, jsonify, url_for, request, make_response, abort, render_template
from flask.ext.login import current_user

from flask_swagger import swagger

from portality.api.v1 import DiscoveryApi, DiscoveryException, jsonify_models, bad_request
from portality.core import app
from portality.decorators import api_key_required

import json

blueprint = Blueprint('api_v1', __name__)

API_VERSION_NUMBER = '1.0.0'

@blueprint.route('/')
def api_spec():
    swag = swagger(app)
    swag['info']['title'] = "DOAJ API documentation"
    # TODO use a Jinja template for the description below, HTML works. Emails use jinja templates already.
    swag['info']['description'] = """
<p>This page documents the first version of the DOAJ API, v.{api_version}</p>
<p>Base URL: <a href="{base_url}" target="_blank">{base_url}</a></p>
<a name="api_desc_search_api" id="api_desc_search_api"></a>

<h2>Search API</h2>

<h3>Friendly field names</h3>

<p>When you are querying on a specific field you can use the json dot notation used by Elasticsearch, so for example to access the journal title of an article, you could use
            <pre>bibjson.journal.title:"Journal of Science"</pre>

<p>Note that all fields are analysed, which means that the above search does not look for the exact string "Journal of Science". To do that, add ".exact" to any string field (not date or number fields) to match the exact contents:</p>
            <pre>bibjson.journal.title.exact:"Journal of Science"</pre>
</p>

<h3>The query string - advanced usage</h3>

<p>The format of the query part of the URL is that of a Lucene query string, as documented here: <a href="https://lucene.apache.org/core/2_9_4/queryparsersyntax.html">https://lucene.apache.org/core/2_9_4/queryparsersyntax.html</a></p>

<p>Some of the lucene query syntax has been disabled in order to prevent queries which may damage performance.  The disabled features are:</p>

<ol>
<li><p>Wildcard searches.  You may not put a * into a query string: <a href="https://lucene.apache.org/core/2_9_4/queryparsersyntax.html#Wildcard Searches">https://lucene.apache.org/core/2_9_4/queryparsersyntax.html#Wildcard Searches</a></p></li>
<li><p>Fuzzy Searches.  You may not use the ~ notation: <a href="https://lucene.apache.org/core/2_9_4/queryparsersyntax.html#Fuzzy Searches">https://lucene.apache.org/core/2_9_4/queryparsersyntax.html#Fuzzy Searches</a></p></li>
<li><p>Proximity Searches. <a href="https://lucene.apache.org/core/2_9_4/queryparsersyntax.html#Proximity Searches">https://lucene.apache.org/core/2_9_4/queryparsersyntax.html#Proximity Searches</a></p></li>
</ol>

<h3>Sorting of results</h3>

<p>Each request can take a "sort" url parameter, which can be of the form of one of:</p>

<pre>
sort=field
sort=field:direction
</pre>

<p>The field again uses the dot notation.</p>

<p>If specifying the direction, it must be one of "asc" or "desc". If no direction is supplied then "asc" is used.</p>

<p>So for example</p>

<pre>
sort=bibjson.title
sort=bibjson.title:desc
</pre>

<p>Note that for fields which may contain multiple values (i.e. arrays), the sort will use the "smallest" value in that field to sort by (depending on the definition of "smallest" for that field type)</p>

""".format(
        api_version=API_VERSION_NUMBER,
        base_url=url_for('.api_spec', _external=True)
    )
    swag['info']['version'] = API_VERSION_NUMBER

    return make_response((jsonify(swag), 200, {'Access-Control-Allow-Origin': '*'}))

@blueprint.route('/docs')
def docs():
    return render_template('doaj/api_docs.html')

@blueprint.route("/search/applications/<path:search_query>")
@api_key_required
def search_applications(search_query):
    """
    Search your applications [Authenticated, not public]
    ---
    tags:
      - search
    description: "Search your applications to the DOAJ"
    parameters:
      -
        name: "search_query"
        in: "path"
        required: true
        type: "string"
      -
        name: "page"
        in: "query"
        required: false
        type: "integer"
      -
        name: "pageSize"
        in: "query"
        required: false
        type: "integer"
      -
        name: "sort"
        in: "query"
        required: false
        type: "string"
      -
        name: "api_key"
        in: "query"
        required: true
        type: "string"
    responses:
      200:
        description: Search results
      400:
        description: Bad Request
    """
    # get the values for the 2 other bits of search info: the page number and the page size
    page = request.values.get("page", 1)
    psize = request.values.get("pageSize", 10)
    sort = request.values.get("sort")

    # check the page is an integer
    try:
        page = int(page)
    except:
        return bad_request("Page number was not an integer")

    # check the page size is an integer
    try:
        psize = int(psize)
    except:
        return bad_request("Page size was not an integer")

    try:
        results = DiscoveryApi.search_applications(current_user, search_query, page, psize, sort)
    except DiscoveryException as e:
        return bad_request(e.message)

    return jsonify_models(results)

@blueprint.route('/search/journals/<path:search_query>')
def search_journals(search_query):

    """
    Search for journals
    ---
    tags:
      - search
    parameters:
      -
        name: search_query
        description:
            <div class="search-query-docs">
            What you are searching for, e.g. computers
            <br>
            <br>
            For convenience we also offer shorter field names for you to use when querying. Note that you cannot use the ".exact" notation mentioned above on these substitutions. The substitutions for articles are as follows:<br>
            <ul>
            <li>title - search within the journal's title</li>
            <li>issn - the journal's issn</li>
            <li>publisher - the journal's publisher (not exact match)</li>
            <li>license - the exact licence</li>
            </ul>
            E.g. you can search for
            <pre>issn:1874-9496</pre>
            <pre>license:CC-BY</pre>
            </div>
        in: path
        required: true
        type: string
      -
        name: page
        description: Which page of the results you wish to see.
        in: query
        required: false
        type: integer
      -
        name: pageSize
        description: How many results per page you wish to see, the default is 10.
        in: query
        required: false
        type: integer
      -
        name: "sort"
        in: "query"
        description:
            <div>
            Substitutions are also available here for convenience
            <ul>
            <li>title - order by the normalised, unpunctuated version of the title</li>
            <li>issn - sort by issn</li>
            </ul>
            For example
            <pre>title:asc</pre>
            <pre>issn:desc</pre>
            </div>
        required: false
        type: "string"
    responses:
      200:
        schema:
          title: Journal search
          properties:
            pageSize:
              type: integer
            timestamp:
              type: string
              format: dateTime
            results:
              type: array
              items:
                type: object
                title: Journal
                properties:
                  last_updated:
                    type: string
                    format: dateTime
                  id:
                    type: string
                  bibjson:
                    type: object
                    title: bibjson
                    properties:
                      publisher:
                        type: string
                      author_pays:
                        type: string
                      license:
                        type: array
                        items:
                          type: object
                          title: license
                          properties:
                            title:
                              type: string
                            url:
                              type: string
                            NC:
                              type: boolean
                            ND:
                              type: boolean
                            embedded_example_url:
                              type: string
                            SA:
                              type: boolean
                            type:
                              type: string
                            BY:
                              type: boolean
                      title:
                        type: string
                      author_pays_url:
                        type: string
                      country:
                        type: string
                      link:
                        type: array
                        items:
                          type: object
                          title: link
                          properties:
                            url:
                              type: string
                            type:
                              type: string
                      provider:
                        type: string
                      keywords:
                        type: array
                        items:
                            type: string
                      oa_start:
                        type: object
                      identifier:
                        type: array
                        items:
                          type: object
                          title: identifier
                          properties:
                            type:
                              type: string
                            id:
                              type: string
                      subject:
                        type: array
                        items:
                          type: object
                          title: subject
                          properties:
                            code:
                              type: string
                            term:
                              type: string
                            scheme:
                              type: string
                  created_date:
                    type: string
                    format: dateTime
            query:
              type: string
            total:
              type: integer
            page:
              type: integer
      400:
        description: Bad Request
    """
    # get the values for the 2 other bits of search info: the page number and the page size
    page = request.values.get("page", 1)
    psize = request.values.get("pageSize", 10)
    sort = request.values.get("sort")

    # check the page is an integer
    try:
        page = int(page)
    except:
        return bad_request("Page number was not an integer")

    # check the page size is an integer
    try:
        psize = int(psize)
    except:
        return bad_request("Page size was not an integer")

    try:
        results = DiscoveryApi.search_journals(search_query, page, psize, sort)
    except DiscoveryException as e:
        return bad_request(e.message)

    return jsonify_models(results)

@blueprint.route('/search/articles/<path:search_query>')
def search_articles(search_query):
    """
    Search for articles
    ---
    tags:
      - search
    notes: This is a longer string of important things
    parameters:
      -
        name: search_query
        description:
            <div class="search-query-docs">
            What you are searching for, e.g. computers
            <br>
            <br>
            For convenience we also offer shorter field names for you to use when querying. Note that you cannot use the ".exact" notation mentioned above on these substitutions. The substitutions for articles are as follows:<br>
            <ul>
            <li>title - search within the article title</li>
            <li>doi - the article's doi</li>
            <li>issn - the article's journal's issn</li>
            <li>publisher - the article's journal's publisher (not exact match)</li>
            <li>abstract - search within the article abstract</li>
            </ul>
            E.g. you can search for
            <pre>doi:10.3389/fpsyg.2013.00479</pre>
            <pre>title:hydrostatic pressure</pre>
            </div>
        in: path
        required: true
        type: string
      -
        name: page
        description: Which page of the results you wish to see.
        in: query
        required: false
        type: integer
      -
        name: pageSize
        description: How many results per page you wish to see, the default is 10.
        in: query
        required: false
        type: integer
      -
        name: sort
        description:
            <div>
            Substitutions are also available here for convenience
            <ul>
            <li>title - order by the normalised, unpunctuated version of the title</li>
            </ul>
            For example
            <pre>title:asc</pre>
            </div>
        in: query
        required: false
        type: string
    responses:
      200:
        schema:
          title: Article search
          properties:
            pageSize:
              type: integer
            timestamp:
              type: string
              format: dateTime
            results:
              type: array
              items:
                type: object
                title: Article
                properties:
                  last_updated:
                    type: string
                    format: dateTime
                  id:
                    type: string
                  bibjson:
                    type: object
                    title: bibjson
                    properties:
                      identifier:
                        type: array
                        items:
                          type: object
                          title: identifier
                          properties:
                            type:
                              type: string
                            id:
                              type: string
                      start_page:
                        type: integer
                      title:
                        type: string
                      journal:
                        type: object
                        title: journal
                        properties:
                          publisher:
                            type: string
                          language:
                            type: array
                            items:
                              type: string
                          license:
                            type: array
                            items:
                              type: object
                              title: license
                              properties:
                                url:
                                  type: string
                                type:
                                  type: string
                                title:
                                  type: string
                          title:
                            type: string
                          country:
                            type: string
                          number:
                            type: integer
                          volume:
                            type: integer
                      author:
                        type: array
                        items:
                          type: object
                          title: author
                          properties:
                            affiliation:
                              type: string
                            email:
                              type: string
                            name:
                              type: string
                      month:
                        type: integer
                      link:
                        type: array
                        items:
                          type: object
                          title: link
                          properties:
                            url:
                              type: string
                            type:
                              type: string
                            content_type:
                              type: string
                      year:
                        type: integer
                      keywords:
                        type: array
                        items:
                            type: string
                      subject:
                        type: array
                        items:
                          type: object
                          title: subject
                          properties:
                            code:
                              type: string
                            term:
                              type: string
                            scheme:
                              type: string
                      abstract:
                        type: string
                      end_page:
                        type: integer
                  created_date:
                    type: string
                    format: dateTime
            query:
              type: string
            total:
              type: integer
            page:
              type: integer
      400:
        description: "Bad Request"
    """

    # get the values for the 2 other bits of search info: the page number and the page size
    page = request.values.get("page", 1)
    psize = request.values.get("pageSize", 10)
    sort = request.values.get("sort")

    # check the page is an integer
    try:
        page = int(page)
    except:
        return bad_request("Page number was not an integer")

    # check the page size is an integer
    try:
        psize = int(psize)
    except:
        return bad_request("Page size was not an integer")

    results = None
    try:
        results = DiscoveryApi.search_articles(search_query, page, psize, sort)
    except DiscoveryException as e:
        return bad_request(e.message)

    return jsonify_models(results)
