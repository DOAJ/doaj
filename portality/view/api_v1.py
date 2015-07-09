from flask import Blueprint, jsonify, url_for, request, make_response, abort, render_template
from flask_swagger import swagger

from portality.api.v1 import DiscoveryApi, DiscoveryException, jsonify_models
from portality.core import app

import json

blueprint = Blueprint('api_v1', __name__)

def _bad_request(message=None, exception=None):
    if exception is not None:
        message = exception.message
    app.logger.info("Sending 400 Bad Request from client: {x}".format(x=message))
    resp = make_response(json.dumps({"status" : "error", "error" : message}))
    resp.mimetype = "application/json"
    resp.status_code = 400
    return resp

@blueprint.route('/spec')
def api_spec():
    swag = swagger(app)
    swag['info']['title'] = "DOAJ API documentation"
    swag['info']['description'] = "This page documents the first version of the DOAJ API."

    return make_response((jsonify(swag), 200, {'Access-Control-Allow-Origin': '*'}))

@blueprint.route('/')
def list_operations():
    # todo use reflection or something
    return jsonify({'available_operations': [
        {
            'description': "Search for journals and articles",
            'base_url': request.base_url + 'search',
            'docs_url': url_for('.docs', _anchor='search', _external=True)
        }
    ]})

@blueprint.route('/docs')
def docs():
    return render_template('doaj/api_docs.html')

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
        description: What you are searching for, e.g. computers
        in: path
        required: true
        type: string
      -
        name: page
        description: Which page of the results you wish to see. This field is optional.
        in: path
        required: false
        type: integer
      -
        name: pageSize
        description: How many results per page you wish to see, the default is 100.
        in: path
        required: false
        type: integer
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
                            terms:
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

    # check the page is an integer
    try:
        page = int(page)
    except:
        return _bad_request("Page number was not an integer")

    # check the page size is an integer
    try:
        psize = int(psize)
    except:
        return _bad_request("Page size was not an integer")

    results = None
    try:
        results = DiscoveryApi.search_journals(search_query, page, psize)
    except DiscoveryException as e:
        return _bad_request(e.message)

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
        description: What you are searching for, e.g. computers
        in: path
        required: true
        type: string
      -
        name: page
        description: Which page of the results you wish to see. This field is optional.
        in: path
        required: false
        type: integer
      -
        name: pageSize
        description: How many results per page you wish to see, the default is 100.
        in: path
        required: false
        type: integer
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
                            terms:
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

    # check the page is an integer
    try:
        page = int(page)
    except:
        return _bad_request("Page number was not an integer")

    # check the page size is an integer
    try:
        psize = int(psize)
    except:
        return _bad_request("Page size was not an integer")

    results = None
    try:
        results = DiscoveryApi.search_articles(search_query, page, psize)
    except DiscoveryException as e:
        return _bad_request(e.message)

    return jsonify_models(results)
