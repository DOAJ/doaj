'''
A simple endpoint for streaming out various bits of data from your index, useful for 
autocompletes and things like that on your front end. Just access indextype/key, 
and use the usual ES params for paging and querying. Returns back a list of values.
'''

import json

from flask import Blueprint, request, abort, make_response

from portality.core import app
import portality.models as models


blueprint = Blueprint('stream', __name__)

# implement a JSON stream that can be used for autocompletes
# index type and key to choose should be provided, and can be comma-separated lists
# "q" param can provide query term to filter by
# "counts" param indicates whether to return a list of strings or a list of lists [string, count]
# "size" can be set to get more back
@blueprint.route('/')
@blueprint.route('/<index>')
@blueprint.route('/<index>/<key>')
def stream(index='record',key='tags',size=1000):

    if index in app.config['NO_QUERY']: abort(401)
    indices = []
    for idx in index.split(','):
        if idx not in app.config['NO_QUERY']:
            indices.append(idx)

    if not isinstance(key,list):
        keys = key.split(',')

    q = request.values.get('q','*')
    if not q.endswith("*"): q += "*"
    if not q.startswith("*"): q = "*" + q

    qry = {
        'query':{'match_all':{}},
        'size': 0,
        'facets':{}
    }
    for ky in keys:
        qry['facets'][ky] = {"terms":{"field":ky+app.config['FACET_FIELD'],"order":request.values.get('order','term'), "size":request.values.get('size',size)}}
    
    klass = getattr(models, index[0].capitalize() + index[1:] )
    r = klass().query(q=qry)

    res = []
    try:
        if request.values.get('counts',False):
            for k in keys:
                res = res + [[i['term'],i['count']] for i in r['facets'][k]["terms"]]
        else:
            for k in keys:
                res = res + [i['term'] for i in r['facets'][k]["terms"]]
    except:
        pass

    resp = make_response( json.dumps(res) )
    resp.mimetype = "application/json"
    return resp

