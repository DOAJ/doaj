'''
An auth-controlled access and retrieval mechanism for a media folder
'''

import json, os

from flask import Blueprint, request, url_for, flash, redirect, abort, make_response
from flask import render_template
from flask.ext.login import current_user

import werkzeug

from portality.core import app
import portality.util as util
import portality.models as models



blueprint = Blueprint('media', __name__)


mediadir = os.path.dirname(os.path.abspath(__file__)).replace('/portality/view','/') + app.config['MEDIA_FOLDER']
if not os.path.exists(mediadir):
    os.makedirs(mediadir)

@blueprint.route('.json')
@blueprint.route('/')
def media():
    listing = os.listdir( mediadir )
    listing = sorted(listing, key=str.lower)
    if util.request_wants_json():
        response = make_response( json.dumps(listing,"","    ") )
        response.headers["Content-type"] = "application/json"
        return response
    else:
        usedin = {}
        for f in listing:
            # see if it is used in any records
            #try:
            r = models.Pages().query(q='*' + f + '*')
            usedin[f] = [i['_source']['url'] for i in r.get('hits',{}).get('hits',[])]
            #except:
            #    usedin[f] = []
        return render_template('media/media.html', files=listing, usedin=usedin)



@blueprint.route('/<path:path>', methods=['GET','POST','DELETE'])
def medias(path=''):
    if request.method == 'GET':
        # NOTE: this is only an alternative for when running in debug mode - it delivers images from media folder successfully
        # otherwise you should set your web server (nginx, apache, whatever) to serve GETs on /media/.*
        loc = mediadir + '/' + path
        if app.config['DEBUG'] and os.path.isfile(loc):
            response = make_response(open(loc).read())
            response.headers["Content-type"] = "image"
            return response
        else:
            abort(404)
    
    elif ( ( request.method == 'DELETE' or ( request.method == 'POST' and request.form.get('submit',False) == 'Delete' ) ) and not current_user.is_anonymous() ):
        try:
            loc = mediadir + '/' + path
            if os.path.isfile(loc):
                os.remove(loc)
        except:
            pass
        return ''

    elif request.method == 'POST' and not current_user.is_anonymous():
        # TODO: check the file type meets the allowed ones, and if so put it in media dir
        filename = werkzeug.secure_filename(path)
        out = open(mediadir + '/' + filename, 'w')
        out.write(request.data)
        out.close()
        return ''

    else:
        abort(401)    

