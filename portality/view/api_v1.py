from flask import Blueprint, jsonify, url_for, request, make_response, abort, render_template
from flask.ext.login import current_user

from flask_swagger import swagger

from portality.api.v1 import DiscoveryApi, DiscoveryException, CrudApi, jsonify_models, bad_request
from portality.core import app
from portality.decorators import api_key_required, api_key_optional

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
<h2 id="intro">Using this live documentation page</h2>
This page contains a list of all routes available via the DOAJ API. It also serves as a live demo page. You can fill in the parameters needed by the API and it will construct and send a request to the live API for you, letting you see all the details you might need for your integration. Please note that not all fields will be available on all records. Further information on advanced usage of the routes is available at the bottom below the route list.

<h2 id="intro_auth">Authenticated routes</h2>
<p>Note that some routes require authentication and are only available to publishers who submit data to DOAJ or other collaborators who integrate more closely with DOAJ. If you think you could benefit from integrating more closely with DOAJ by using these routes, please <a href="{contact_us_url}">contact us</a>.</p>
""".format(
        api_version=API_VERSION_NUMBER,
        base_url=url_for('.api_spec', _external=True),
        contact_us_url=url_for('doaj.contact')
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
    Search your applications <span class="red">[Authenticated, not public]</span>
    ---
    tags:
      - search
    parameters:
      -
        name: api_key
        description: <div class="search-query-docs"> Go to the top right of the page and click your username. If you have generated an API key already, it will appear under your name. If not, click the Generate API Key button. Accounts are not available to the public. <a href="#intro_auth">More details</a></div>
        in: query
        required: true
        type: string
      -
        name: search_query
        description:
            <div class="search-query-docs">
            What you are searching for, e.g. computers
            <br>
            <br>
            You can search inside any field you see in the results or the schema. <a href="#specific_field_search">More details</a>
            <br>
            For example, to search for all journals tagged with the keyword "heritage"
            <pre>bibjson.keywords:heritage</pre>
            <a href="#short_field_names">Short-hand names are available</a> for some fields
            <pre>issn:1874-9496</pre>
            <pre>publisher:dove</pre>
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
        in: query
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
        type: string
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
                      alternative_title:
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
                      institution:
                        type: string
                      keywords:
                        type: array
                        items:
                            type: string
                      oa_start:
                        type: object
                        title: oa_start
                        properties:
                          year:
                            type: string
                          volume:
                            type: string
                          number:
                            type: string
                      oa_end:
                        type: object
                        title: oa_end
                        properties:
                          year:
                            type: string
                          volume:
                            type: string
                          number:
                            type: string
                      apc_url:
                        type: string
                      apc:
                        type: object
                        title: apc
                        properties:
                          currency:
                            type: string
                          average_price:
                            type: string
                      submission_charges_url:
                        type: string
                      submission_charges:
                        type: object
                        title: apc
                        properties:
                          currency:
                            type: string
                          average_price:
                            type: string
                      archiving_policy:
                        type: object
                        title: archiving_policy
                        properties:
                          policy:
                            type: array
                            items:
                              type: string
                          url:
                            type: string
                      editorial_review:
                        type: object
                        title: editorial_review
                        properties:
                          process:
                            type: string
                          url:
                            type: string
                      plagiarism_detection:
                        type: object
                        title: plagiarism_detection
                        properties:
                          detection:
                            type: boolean
                          url:
                            type: string
                      article_statistics:
                        type: object
                        title: article_statistics
                        properties:
                          statistics:
                            type: boolean
                          url:
                            type: string
                      deposit_policy:
                        type: array
                        items:
                          type: string
                      author_copyright:
                        type: object
                        title: author_copyright
                        properties:
                          copyright:
                            type: string
                          url:
                            type: string
                      author_publishing_rights:
                        type: object
                        title: author_publishing_rights
                        properties:
                          publishing_rights:
                            type: string
                          url:
                            type: string
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
                      allows_fulltext_indexing:
                        type: boolean
                      persistent_identifier_scheme:
                        type: array
                        items:
                          type: string
                      format:
                        type: array
                        items:
                          type: string
                      publication_time:
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
                  suggestion:
                    type: object
                    title: suggestion
                    properties:
                      suggester:
                        type: object
                        title: suggester
                        properties:
                          name:
                            type: string
                          email:
                            type: string
                      suggested_on:
                        type: string
                        format: dateTime
                      articles_last_year:
                        type: object
                        title: articles_last_year
                        properties:
                          count:
                            type: string
                          url:
                            type: string
                      article_metadata:
                        type: boolean

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
            You can search inside any field you see in the results or the schema. <a href="#specific_field_search">More details</a>
            <br>
            For example, to search for all journals tagged with the keyword "heritage"
            <pre>bibjson.keywords:heritage</pre>
            <a href="#short_field_names">Short-hand names are available</a> for some fields
            <pre>issn:1874-9496</pre>
            <pre>publisher:dove</pre>
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
        in: query
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
        type: string
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
                      alternative_title:
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
                      institution:
                        type: string
                      keywords:
                        type: array
                        items:
                            type: string
                      oa_start:
                        type: object
                        title: oa_start
                        properties:
                          year:
                            type: string
                          volume:
                            type: string
                          number:
                            type: string
                      oa_end:
                        type: object
                        title: oa_end
                        properties:
                          year:
                            type: string
                          volume:
                            type: string
                          number:
                            type: string
                      apc_url:
                        type: string
                      apc:
                        type: object
                        title: apc
                        properties:
                          currency:
                            type: string
                          average_price:
                            type: string
                      submission_charges_url:
                        type: string
                      submission_charges:
                        type: object
                        title: apc
                        properties:
                          currency:
                            type: string
                          average_price:
                            type: string
                      archiving_policy:
                        type: object
                        title: archiving_policy
                        properties:
                          policy:
                            type: array
                            items:
                              type: string
                          url:
                            type: string
                      editorial_review:
                        type: object
                        title: editorial_review
                        properties:
                          process:
                            type: string
                          url:
                            type: string
                      plagiarism_detection:
                        type: object
                        title: plagiarism_detection
                        properties:
                          detection:
                            type: boolean
                          url:
                            type: string
                      article_statistics:
                        type: object
                        title: article_statistics
                        properties:
                          statistics:
                            type: boolean
                          url:
                            type: string
                      deposit_policy:
                        type: array
                        items:
                          type: string
                      author_copyright:
                        type: object
                        title: author_copyright
                        properties:
                          copyright:
                            type: string
                          url:
                            type: string
                      author_publishing_rights:
                        type: object
                        title: author_publishing_rights
                        properties:
                          publishing_rights:
                            type: string
                          url:
                            type: string
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
                      allows_fulltext_indexing:
                        type: boolean
                      persistent_identifier_scheme:
                        type: array
                        items:
                          type: string
                      format:
                        type: array
                        items:
                          type: string
                      publication_time:
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
            You can search inside any field you see in the results or the schema. <a href="#specific_field_search">More details</a>
            <br>
            For example, to search for all articles with abstracts containing the word "shadow"
            <pre>bibjson.abstract:"shadow"</pre>
            <a href="#short_field_names">Short-hand names are available</a> for some fields
            <pre>doi:10.3389/fpsyg.2013.00479</pre>
            <pre>issn:1874-9496</pre>
            <pre>license:CC-BY</pre>
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
                            type: string
                          volume:
                            type: string
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
                            content_type:
                              type: string
                      year:
                        type: string
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


@api_key_optional
@blueprint.route('/journals/<jid>')
def retrieve_journal(jid):
    # depending on current_user being there or not, call one of these
    j = CrudApi.retrieve_public_journal(jid)
    # OR
    j = CrudApi.retrieve_auth_journal(jid, current_user)

    return jsonify_models(j)

    # also consider: Somebody is authenticated but tries to access a journal
    # that is not theirs. In that case, return 404 Not Found.
    # You should make portality.api.v1.crud.journals.JournalsCrudApi#retrieve_auth_journal
    # return an appropriate value in that case (None is fine) and cause a 404 here in the view

    # then finally, consider handling if the journal id we're given really
    # is not found - should also result in 404 Not Found

    # ideally (bonus points) if the id is malformed (check elasticsearch id format)
    # then return 400 Bad Request

    # there are helpers you can use as-is in the view route to generate 400 Bad Request and 404 Not Found:
    # not_found(message)
    # bad_request(message)