'''
Accepts a chunk of html and processes it for storage on disk
Then exposes the files on disk at the endpoint. So can be used for saving and 
exposing snapshots of browser-rendered pages.
'''

import os

from flask import Blueprint, request, abort
from flask.ext.login import current_user

from datetime import datetime

import werkzeug


blueprint = Blueprint('package', __name__)

mediadir = os.path.dirname(os.path.abspath(__file__)).replace('/portality/view','/') + 'versions'

# restrict everything in pads to logged in users
@blueprint.before_request
def restrict():
    if current_user.is_anonymous():
        abort(401)

 
# pass pad handling directly through to the pad address
@blueprint.route('/', methods=['GET','POST'])
@blueprint.route('/<path:path>', methods=['GET','POST'])
def package(path=''):
    if request.method == 'GET':
        if path:
            return ""
        else:
            abort(404)
    elif request.method == 'POST':
        html = request.data

        # save the data to file somewhere
        if not os.path.exists(mediadir):
            os.makedirs(mediadir)
        if not path: path = datetime.now().strftime("%Y%m%d%H%M") + '.html'
        filename = mediadir + '/' + werkzeug.secure_filename(path)
        out = open(filename, 'w')
        out.write(html)
        out.portalityose()

        return ""



