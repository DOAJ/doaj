'''
A deduplication endpoint for when URLs for accessing records clash
'''

import os

from flask import Blueprint, request, abort

from portality.core import app
import portality.models as models

blueprint = Blueprint('deduplicate', __name__)


@blueprint.route('/', methods=['GET', 'POST'])
def deduplicate(path='',duplicates=[],target='/'):
    if current_user.is_anonymous():
        abort(401)
    elif request.method == 'GET':
        jsitem = deepcopy(app.config['JSITE_OPTIONS'])
        jsitem['facetview']['initialsearch'] = False
        return render_template('deduplicate.html', jsite_options=json.dumps(jsitem), duplicates=duplicates, url=target)
    elif request.method == 'POST':
        for k,v in request.values.items():
            if v and k not in ['url', 'submit']:
                if k.startswith('delete_'):
                    rec = models.Record.pull(k.replace('delete_',''))
                    if rec is not None: rec.delete()
                else:
                    rec = models.Record.pull(k)
                    rec.data['url'] = v
                    rec.save()
        if 'url' in request.values: target = request.values['url']
        return redirect(target)

