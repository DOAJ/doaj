import json
from portality.core import app
from flask import request

class Api(object):
    pass

class ModelJsonEncoder(json.JSONEncoder):
    def default(self, o):
        return o.data

def jsonify_models(models):
    callback = request.args.get('callback', False)
    data = json.dumps(models, cls=ModelJsonEncoder)
    if callback:
        content = str(callback) + '(' + str(data) + ')'
        return app.response_class(content, 200, {'Access-Control-Allow-Origin': '*'}, mimetype='application/javascript')
    else:
        return app.response_class(data, 200, {'Access-Control-Allow-Origin': '*'}, mimetype='application/json')