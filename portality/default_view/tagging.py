import json, time

from flask import Blueprint, request, render_template, flash
from flask.ext.login import current_user
from copy import deepcopy

from portality.core import app
import portality.util as util
import portality.models


blueprint = Blueprint('tagging', __name__)

# restrict everything to logged in users
@blueprint.before_request
def restrict():
    if current_user.is_anonymous():
        abort(401)

@blueprint.route('/', methods=['GET','POST'])
def index():
    js = deepcopy(app.config['JSITE_OPTIONS'])
    js['facetview']['initialsearch'] = False
    js['editable'] = False
    js['data'] = {}
    
    if request.method == 'POST':
        print request.values
        updatecount = 0
        for k,v in request.values.items():
            if k.startswith('id_'):
                kid = k.replace('id_','')
                rec = portality.models.Record.pull(kid)
                print kid
                if rec is not None:
                    print rec.data
                    if request.values['submit'] == 'Delete selected' and request.values.get('selected_' + kid,False):
                        rec.delete()
                        updatecount += 1
                    else:
                        update = False
                        if 'title_'+kid in request.values:
                            if rec.data.get('title','') != request.values['title_'+kid]:
                                update = True
                                rec.data['title'] = request.values['title_'+kid]
                        if 'excerpt_'+kid in request.values: 
                            if rec.data.get('excerpt','') != request.values['excerpt_'+kid]:
                                update = True
                                rec.data['excerpt'] = request.values['excerpt_'+kid]
                        if 'url_'+kid in request.values: 
                            if rec.data.get('url','') != request.values['url_'+kid]:
                                update = True
                                rec.data['url'] = request.values['url_'+kid]

                        # check if the tag values are in the box from select2
                        if 'tags_'+kid in request.values:
                            tgs = []
                            for t in request.values['tags_'+kid].split(','):
                                if len(t) > 0 : tgs.append(t)
                            if rec.data.get('tags',[]) != tgs:
                                update = True
                                rec.data['tags'] = tgs

                        if update:
                            rec.save()
                            updatecount += 1

        time.sleep(1)
        if request.values['submit'] == 'Delete selected':
            method = 'deleted'
        else:
            method = 'updated'
        flash(str(updatecount) + " records have been " + method + ".")
        
    return render_template('tagging/tagging.html', jsite_options=json.dumps(js), offline=js['offline'])


