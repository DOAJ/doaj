import json, uuid
from portality.core import app
from flask import request
from copy import deepcopy

ERROR_TEMPLATE = {"status": {"type": "string"}, "error": {"type": "string"}}
CREATED_TEMPLATE = {"status": {"type": "string"}, "id": {"type": "string"}, "location": {"type": "string"}}

class Api(object):
    pass


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
