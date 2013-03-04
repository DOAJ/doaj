'''
Presents a page by which to bulk control tags applied to records.
Also handles submission of updates to those tags for the records.
'''


import json
from copy import deepcopy

from flask import Blueprint, request, render_template, flash
from flask.ext.login import current_user

from portality.core import app
import portality.models as models


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
        for k,v in request.values.items():
            if k.startswith('id_'):
                kid = k.replace('id_','')
                rec = models.Record.pull(kid)
                if rec is not None:
                    if 'delete_'+kid in request.values:
                        rec.delete()
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

                        if 'accessible_'+kid in request.values and not rec.data.get('accessible',False):
                            update = True
                            rec.data['accessible'] = True
                        elif rec.data.get('accessible',False) and not 'accessible_'+kid in request.values:
                            update = True
                            rec.data['accessible'] = False

                        # check if the tag values are in the box from select2
                        if 'tags_'+kid in request.values:
                            tgs = []
                            for t in request.values['tags_'+kid].split(','):
                                if len(t) > 0 : tgs.append(t)
                            if rec.data.get('tags',[]) != tgs:
                                update = True
                                rec.data['tags'] = tgs

                        if update: rec.save()

        flash("Updated. If you don't see your updates yet, <a href=\"/tagging\">refresh</a> the page.")
        
    records = [i['_source'] for i in models.Record.query(size=100000,sort={'url.exact':{'order':'asc'}}).get('hits',{}).get('hits',[])]
    return render_template('tagging.html', jsite_options=json.dumps(js), records=records, offline=js['offline'])


