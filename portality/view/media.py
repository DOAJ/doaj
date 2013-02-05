'''
An auth-controlled access and retrieval mechanism for a media folder
'''

import json, os
from copy import deepcopy

from flask import Blueprint, request, abort, make_response, render_template
from flask.ext.login import current_user

import werkzeug

from portality.core import app
import portality.util as util


blueprint = Blueprint('media', __name__)


mediadir = os.path.dirname(os.path.abspath(__file__)).replace('/portality/view','/') + app.config['MEDIA_FOLDER']

@blueprint.route('/')
def media():
    jsite = deepcopy(app.config['JSITE_OPTIONS'])
    jsite['data'] = False
    jsite['editable'] = False
    jsite['facetview']['initialsearch'] = False
    listing = os.listdir( mediadir )
    if util.request_wants_json():
        response = make_response( json.dumps(listing,"","    ") )
        response.headers["Content-type"] = "application/json"
        return response
    else:
        # TODO: add some sort of delete and other functionality to the media page display...
        files = ''
        for f in listing:
            if f.split('.')[-1] in ['png','jpg','jpeg','gif']:
                files += '<a rel="gallery" class="span2 thumbnail" href="/' + app.config['MEDIA_FOLDER'] + '/'
                files += f + '"><img src="/' + app.config['MEDIA_FOLDER'] + '/' + f + '" /></a>'
            else:
                files += '<div class="span2 thumbnail"><h3><a _target="blank" href="/' 
                files += app.config['MEDIA_FOLDER'] + '/' + f + '">' + f + '</a></h3></div>'
        return render_template('media/media.html', jsite_options=json.dumps(jsite), files=files, nosettings=True)


@blueprint.route('/<path:path>', methods=['GET','POST'])
def medias(path=''):
    # TODO: this should be a setting on the nginx server
    if request.method == 'GET':
        loc = mediadir + '/' + path
        #if app.config['DEBUG'] and os.path.isfile(loc):
        if os.path.isfile(loc):
            response = make_response(open(loc).read())
            response.headers["Content-type"] = "image"
            return response
        else:
            abort(404)
    
    elif request.method == 'POST':
        if not current_user.is_anonymous():
            # TODO: check the file type meets the allowed ones, and if so put it in media dir
            filename = werkzeug.secure_filename(path)
            out = open(mediadir + '/' + filename, 'w')
            out.write(request.data)
            out.close()
            return ''
        else:
            abort(401)    

