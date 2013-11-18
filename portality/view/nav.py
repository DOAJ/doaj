'''
An endpoint for exposing a sitemap generated from records in the index.
Needs work - functional but not great.
Needs updating to expose XML too.
'''

import json

from flask import Blueprint, request, url_for, flash, redirect, abort
from flask import render_template, make_response
from flask.ext.login import current_user

from portality.core import app
import portality.util as util
import portality.models as models


blueprint = Blueprint('nav', __name__)


@blueprint.route('/', methods=['GET','POST'])
def index():

    if current_user.is_anonymous():
        return render_template('nav/index.html')
    else:
        if request.method == 'POST' and request.values.get('nav','') != '':
            out = open('portality/templates/nav/nav.html','w')
            out.write(request.values['nav'])
            out.close()
            flash('Site navigation has been updated')

        return render_template('nav/index.html', public=False)

@blueprint.route('.xml')
def xml():
    resp = render_template('nav/sitemap.xml')
    resp.mimetype = "application/xml"
    return resp

def generate_sitemap_xml(sitemap=False):
     # TODO: finish this, have it meet google sitemap / resourcesync reqs
     # add anything necessary to handle versioning for resourcesync above too
    pass
    

