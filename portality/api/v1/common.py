import json, uuid
from portality.core import app
from flask import request
from copy import deepcopy

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
    R201_BULK = {"schema": {"properties": CREATED_TEMPLATE, "description": "Resource created successfully, response contains the new resource ID and location."}}
    R204 = {"description": "OK (Request succeeded), No Content"}
    R400 = {"schema": {"properties": ERROR_TEMPLATE}, "description": "Bad Request. Your request body was missing a required field, or the data in one of the fields did not match the schema above (e.g. string of latin letters in an integer field). In the Bulk API it may mean that one of the records in the bulk operation failed. See the \"error\" part of the response for details."}
    R401 = {"schema": {"properties": ERROR_TEMPLATE}, "description": "Access to this route/resource requires authentication, but you did not provide any credentials."}
    R403 = {"schema": {"properties": ERROR_TEMPLATE}, "description": "Access to this route/resource requires authentication, and you provided the wrong credentials. This includes situations where you are authenticated successfully via your API key, but you are not the owner of a specific resource and are therefore barred from updating/deleting it."}
    R404 = {"schema": {"properties": ERROR_TEMPLATE}, "description": "Resource not found"}

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
    def _build_swag_response(cls, template, api_key_optional_override=None):
        """
        Construct the swagger response structure upon a template
        :param template
        :param api_key_optional_override: override the class-level value of API_KEY_OPTIONAL
        :return: an updated template
        """
        template = deepcopy(template)
        cls._add_swag_tag(template)
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
    return respond(data, 200)


def respond(data, status):
    callback = request.args.get('callback', False)
    if callback:
        content = str(callback) + '(' + str(data) + ')'
        return app.response_class(content, status, {'Access-Control-Allow-Origin': '*'}, mimetype='application/javascript')
    else:
        return app.response_class(data, status, {'Access-Control-Allow-Origin': '*'}, mimetype='application/json')


@app.errorhandler(Api400Error)
def bad_request(error):
    magic = uuid.uuid1()
    app.logger.info("Sending 400 Bad Request from client: {x} (ref: {y})".format(x=error.message, y=magic))
    t = deepcopy(ERROR_TEMPLATE)
    t['status'] = 'bad_request'
    t['error'] = error.message + " (ref: {y})".format(y=magic)
    return respond(json.dumps(t), 400)


@app.errorhandler(Api404Error)
def not_found(error):
    magic = uuid.uuid1()
    app.logger.info("Sending 404 Not Found from client: {x} (ref: {y})".format(x=error.message, y=magic))
    t = deepcopy(ERROR_TEMPLATE)
    t['status'] = 'not_found'
    t['error'] = error.message + " (ref: {y})".format(y=magic)
    return respond(json.dumps(t), 404)


@app.errorhandler(Api401Error)
def unauthorised(error):
    magic = uuid.uuid1()
    app.logger.info("Sending 401 Unauthorised from client: {x} (ref: {y})".format(x=error.message, y=magic))
    t = deepcopy(ERROR_TEMPLATE)
    t['status'] = 'unauthorised'
    t['error'] = error.message + " (ref: {y})".format(y=magic)
    return respond(json.dumps(t), 401)


@app.errorhandler(Api403Error)
def forbidden(error):
    magic = uuid.uuid1()
    app.logger.info("Sending 403 Forbidden from client: {x} (ref: {y})".format(x=error.message, y=magic))
    t = deepcopy(ERROR_TEMPLATE)
    t['status'] = 'forbidden'
    t['error'] = error.message + " (ref: {y})".format(y=magic)
    return respond(json.dumps(t), 403)
