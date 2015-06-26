import json
from portality.core import app

class Api(object):
    pass

class ModelJsonEncoder(json.JSONEncoder):
    def default(self, o):
        return o.data

def jsonify_models(models):
    return app.response_class(json.dumps(models, cls=ModelJsonEncoder), 200, {'Access-Control-Allow-Origin': '*'}, mimetype='application/json')