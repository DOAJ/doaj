import json, uuid
from portality.core import app
from flask import request
from copy import deepcopy
from link_header import LinkHeader, Link

LINK_HEADERS = ['next', 'prev', 'last']
TOTAL_RESULTS_COUNT = ['total']

ERROR_TEMPLATE = {"status": {"type": "string"}, "error": {"type": "string"}}
CREATED_TEMPLATE = {"status": {"type": "string"}, "id": {"type": "string"}, "location": {"type": "string"}}


class Api(object):
    SWAG_TEMPLATE = {
        "responses": {},
        "parameters": [],
        "tags": []
    }
    R200 = {"schema": {}}
    R201 = {"schema": {"properties": CREATED_TEMPLATE, "description": "Resource created successfully, response contains the new resource ID and location."}}
    R201_BULK = {"schema": {"items": {"properties" : CREATED_TEMPLATE, "type" : "object"}, "type" : "array", "description": "Resources created successfully, response contains the new resource IDs and locations."}}
    R204 = {"description": "OK (Request succeeded), No Content"}
    R400 = {"schema": {"properties": ERROR_TEMPLATE}, "description": "Bad Request. Your request body was missing a required field, or the data in one of the fields did not match the schema above (e.g. string of latin letters in an integer field). In the Bulk API it may mean that one of the records in the bulk operation failed. See the \"error\" part of the response for details."}
    R401 = {"schema": {"properties": ERROR_TEMPLATE}, "description": "Access to this route/resource requires authentication, but you did not provide any credentials."}
    R403 = {"schema": {"properties": ERROR_TEMPLATE}, "description": "Access to this route/resource requires authentication, and you provided the wrong credentials. This includes situations where you are authenticated successfully via your API key, but you are not the owner of a specific resource and are therefore barred from updating/deleting it."}
    R404 = {"schema": {"properties": ERROR_TEMPLATE}, "description": "Resource not found"}
    R409 = {"schema": {"properties": ERROR_TEMPLATE}, "description": "This resource or one it depends on is currently locked for editing by another user, and you may not submit changes to it at this time"}
    R500 = {"schema": {"properties": ERROR_TEMPLATE}, "description": "Unable to retrieve the recource. This record contains bad data"}

    SWAG_API_KEY_REQ_PARAM = {
        "description": "<div class=\"search-query-docs\"> Go to the top right of the page and click your username. If you have generated an API key already, it will appear under your name. If not, click the Generate API Key button. Accounts are not available to the public. <a href=\"#intro_auth\">More details</a></div>",
        "required": True,
        "type": "string",
        "name": "api_key",
        "in": "query"
    }

    @classmethod
    @property
    def SWAG_TAG(cls):
        raise RuntimeError('You must override this class constant in every subclass.')

    @classmethod
    def _add_swag_tag(cls, template):
        template['tags'].append(cls.SWAG_TAG)
        return template

    @classmethod
    def _add_api_key(cls, template, optional=False):
        api_key_param = deepcopy(cls.SWAG_API_KEY_REQ_PARAM)
        if optional:
            api_key_param['required'] = False
            api_key_param['description'] = "<div class=\"search-query-docs\"><em>Note this parameter is optional for this route - you could, but don't have to supply a key. Doing so grants you access to records of yours that are not public, in addition to all public records.</em> Go to the top right of the page and click your username. If you have generated an API key already, it will appear under your name. If not, click the Generate API Key button. Accounts are not available to the public. <a href=\"#intro_auth\">More details</a></div>"
        template["parameters"].insert(0, api_key_param)
        return template

    @classmethod
    def _build_swag_response(cls, template, api_key_optional_override=None, api_key_override=None):
        """
        Construct the swagger response structure upon a template
        :param template
        :param api_key_optional_override: override the class-level value of API_KEY_OPTIONAL
        :return: an updated template
        """
        template = deepcopy(template)
        cls._add_swag_tag(template)
        if api_key_override is not False:
            if api_key_optional_override is not None:
                cls._add_api_key(template, optional=api_key_optional_override)
            elif hasattr(cls, 'API_KEY_OPTIONAL'):
                cls._add_api_key(template, optional=cls.API_KEY_OPTIONAL)
        return template


class Api400Error(Exception):
    pass


class Api401Error(Exception):
    pass


class Api403Error(Exception):
    pass


class Api404Error(Exception):
    pass


class Api409Error(Exception):
    """
    API error to throw if a resource being edited is locked
    """
    pass


class Api500Error(Exception):
    pass


class DataObjectJsonEncoder(json.JSONEncoder):
    def default(self, o):
        return o.data


class ModelJsonEncoder(json.JSONEncoder):
    def default(self, o):
        return o.data


def created(obj, location):
    app.logger.info("Sending 201 Created: {x}".format(x=location))
    t = deepcopy(CREATED_TEMPLATE)
    t['status'] = "created"
    t['id'] = obj.id
    t['location'] = location
    resp = respond(json.dumps(t), 201)
    resp.headers["Location"] = location
    resp.status_code = 201
    return resp

def bulk_created(ids_and_locations):
    app.logger.info("Sending 201 Created for bulk request")
    out = []
    for id, loc in ids_and_locations:
        t = deepcopy(CREATED_TEMPLATE)
        t['status'] = "created"
        t['id'] = id
        t['location'] = loc
        out.append(t)

    resp = respond(json.dumps(out), 201)
    resp.status_code = 201
    return resp

def no_content():
    return respond("", 204)


def jsonify_data_object(do):
    data = json.dumps(do, cls=DataObjectJsonEncoder)
    return respond(data, 200)


def jsonify_models(models):
    data = json.dumps(models, cls=ModelJsonEncoder)

    metadata = {}
    for k in LINK_HEADERS + TOTAL_RESULTS_COUNT:
        if k in models.data:
            metadata[k] = models.data[k]

    return respond(data, 200, metadata=metadata)

def generate_link_headers(metadata):
    """
    Generate Link: HTTP headers for API navigation.

    :param metadata: Dictionary with none, some or all of the
    keys 'next', 'prev' and 'last' defined. The values are the
    corresponding pre-generated links.
    """
    link_metadata = {k: v for k, v in metadata.items() if k in LINK_HEADERS}

    links = []
    for k, v in link_metadata.items():
        links.append(Link(v, rel=k))  # e.g. Link("http://example.com/foo", rel="next")

    return str(LinkHeader(links))  # RFC compliant headers e.g.
       # <http://example.com/foo>; rel=next, <http://example.com/bar>; rel=last

def respond(data, status, metadata=None):
    # avoid subtle bugs, don't use mutable objects as default vals in Python
    # https://pythonconquerstheuniverse.wordpress.com/category/python-gotchas/
    if metadata is None:
        metadata = {}

    headers = {'Access-Control-Allow-Origin': '*'}
    link = generate_link_headers(metadata)
    if link:
        headers['Link'] = link

    if 'total' in metadata:
        headers['X-Total-Count'] = metadata['total']

    callback = request.args.get('callback', False)
    if callback:
        content = str(callback) + '(' + str(data) + ')'
        return app.response_class(content, status, headers, mimetype='application/javascript')
    else:
        return app.response_class(data, status, headers, mimetype='application/json')


@app.errorhandler(Api400Error)
def bad_request(error):
    magic = uuid.uuid1()
    app.logger.info("Sending 400 Bad Request from client: {x} (ref: {y})".format(x=str(error), y=magic))
    t = deepcopy(ERROR_TEMPLATE)
    t['status'] = 'bad_request'
    t['error'] = str(error) + " (ref: {y})".format(y=magic)
    return respond(json.dumps(t), 400)


@app.errorhandler(Api404Error)
def not_found(error):
    magic = uuid.uuid1()
    app.logger.info("Sending 404 Not Found from client: {x} (ref: {y})".format(x=str(error), y=magic))
    t = deepcopy(ERROR_TEMPLATE)
    t['status'] = 'not_found'
    t['error'] = str(error) + " (ref: {y})".format(y=magic)
    return respond(json.dumps(t), 404)


@app.errorhandler(Api401Error)
def unauthorised(error):
    magic = uuid.uuid1()
    app.logger.info("Sending 401 Unauthorised from client: {x} (ref: {y})".format(x=str(error), y=magic))
    t = deepcopy(ERROR_TEMPLATE)
    t['status'] = 'unauthorised'
    t['error'] = str(error) + " (ref: {y})".format(y=magic)
    return respond(json.dumps(t), 401)


@app.errorhandler(Api403Error)
def forbidden(error):
    magic = uuid.uuid1()
    app.logger.info("Sending 403 Forbidden from client: {x} (ref: {y})".format(x=str(error), y=magic))
    t = deepcopy(ERROR_TEMPLATE)
    t['status'] = 'forbidden'
    t['error'] = str(error) + " (ref: {y})".format(y=magic)
    return respond(json.dumps(t), 403)

@app.errorhandler(Api500Error)
def bad_request(error):
    magic = uuid.uuid1()
    app.logger.info("Sending 500 Bad Request from client: {x} (ref: {y})".format(x=str(error), y=magic))
    t = deepcopy(ERROR_TEMPLATE)
    t['status'] = 'Unable to retrieve the recource.'
    t['error'] = str(error) + " (ref: {y})".format(y=magic)
    return respond(json.dumps(t), 500)
