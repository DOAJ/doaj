
# this runs the Pagemanager endpoint for standard display of web pages

import json, time, requests, urllib, markdown

from flask import Blueprint, request, url_for, abort, make_response, flash
from flask import render_template, redirect
from flask.ext.login import current_user

import portality.util as util
from portality.core import app
import portality.models as models
from portality.view.forms import dropdowns


blueprint = Blueprint('Pagemanager', __name__)


# a method for editing the page
@blueprint.route('/edit', methods=['GET','POST'])
@blueprint.route('/<path:path>/edit', methods=['GET','POST'])
def edit(path='/'):
    if path != '/': path = '/' + path
    record = models.Pages.pull_by_url(path)
    if record is None:
        if current_user.is_anonymous():
            abort(404)
        else:
            return redirect('/' + path)
    elif current_user.is_anonymous():
        pass # check permissions to edit here
    else:
        return render_template('pagemanager/edit.html', record=record)


# a method for managing page settings and creating / deleting pages
@blueprint.route('/settings', methods=['GET','POST'])
@blueprint.route('/<path:path>/settings', methods=['GET','POST','DELETE'])
def settings(path='/'):
    if current_user.is_anonymous():
        abort(401)

    if path != '/': path = '/' + path
    next = util.is_safe_url(request.values.get('next',path))
    record = models.Pages.pull_by_url(next)
    if record is None:
        rec = {
            'url': next,
            'author': current_user.id
        }
    else:
        rec = record.data
        
    if request.method == 'GET':
        if record is None:
            flash('There is no page here yet - create one.')
        return render_template(
            'pagemanager/settings.html', 
            tags = json.dumps(dropdowns('pagemanager','tags')),
            urls = json.dumps(dropdowns('pagemanager','url')),
            record = rec
        )

    elif (  request.method == 'DELETE' or 
            (request.method == 'POST' and 
            request.values.get('submit',False) == 'Delete') ):
        if record is None:
            abort(404)
        else:
            record.delete()
            flash('Page deleted')
            return redirect("/")

    elif request.method == 'POST':
        if record is None:
            record = models.Pages()
            if request.values.get('template',False):
                tmpl = models.Pages.pull_by_url(request.values['template'])
                if tmpl is not None and 'content' in tmpl.data:
                    record.data['content'] = tmpl.data['content']
        
        newdata = request.json if request.json else request.values
        # check the new url does not overwrite an already present url
        if 'url' not in newdata:
            flash("A URL is required.")
        elif (record.data.get('url','') != newdata['url'] and 
                models.Pages.pull_by_url(newdata['url']) is not None ):
            # update record data so form is up to date but don't save it
            record.update_from_form(request)
            flash("There is already a page present at the URL you specifed. You must delete that page first.")
        else:
            record.save_from_form(request)
            flash('Settings updated')
            time.sleep(1)

        return render_template(
            'pagemanager/settings.html', 
            tags = json.dumps(dropdowns('pages','tags')),
            urls = json.dumps(dropdowns('pages','url')),
            record = record.data
        )


@blueprint.route('/manage', methods=['GET','POST'])
def manage():
    
    if request.method == 'POST':
        updatecount = 0
        for k,v in request.values.items():
            if k.startswith('id_'):
                kid = k.replace('id_','')
                rec = models.Pages.pull(kid)
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
        
    return render_template('pagemanager/manage.html')


# this is a catch-all that allows us to present everything as a search
@blueprint.route('/', methods=['GET','POST','DELETE'])
@blueprint.route('/<path:path>', methods=['GET','POST','DELETE'])
def pagemanager(path=''):

    url = '/' + path.lstrip('/').rstrip('/')
    if url.endswith('.json'): url = url.replace('.json','')
    rec = models.Pages.pull_by_url(url)
        
    if request.method == 'GET':
        if util.request_wants_json():
            if ( not rec or ( current_user.is_anonymous() and 
                    not app.config.get('PUBLIC_ACCESSIBLE_JSON',True) ) ):
                abort(404)
            resp = make_response( rec.json )
            resp.mimetype = "application/json"
            return resp

        # build the content
        if rec is not None:
            if ( not rec.data.get('accessible',False) and 
                    current_user.is_anonymous() ):
                abort(401)

            content = ''

            # TODO: retrieve from file on disk
            # TODO: pass through jinja processor
            # can be done by passing the file as a render param called child and having an include child statement in the template
            # would need to check last modified of es record, file on disk, and etherpad page
            
            # update content from collaborative pad
            if app.config.get('COLLABORATIVE',False):
                a = app.config['COLLABORATIVE'].rstrip('/') + '/p/'
                a += rec.id + '/export/txt'
                c = requests.get(a)
                if rec.data.get('content',False) != c.text:
                    rec.data['content'] = c.text
                    rec.save()
            content += markdown.markdown( rec.data.get('content','') )

            # if an embedded file url has been provided, embed it in content
            if rec.data.get('embed', False):
                if ( rec.data['embed'].find('/pub?') != -1 or 
                        rec.data['embed'].find('docs.google.com') != -1 ):
                    content += '<iframe id="embedded" src="' + rec.data['embed']
                    content += '" width="100%" height="1000" '
                    content += 'style="border:none;"></iframe>'
                else:
                    content += '<iframe id="embedded" '
                    content += 'src="http://docs.google.com/viewer?url='
                    content += urllib.quote_plus(rec.data['embed']) 
                    content += '&embedded=true" width="100%" height="1000" '
                    content += 'style="border:none;"></iframe>'
            
            if 'content' in rec.data: del rec.data['content']
            return render_template(
                'pagemanager/index.html', 
                content=content, 
                record=rec
            )

        elif current_user.is_anonymous():
            abort(404)
        else:
            if url == '/':
                return redirect(url_for('.settings'))
            else:
                return redirect(url + url_for('.settings'))
        
    elif request.method == 'POST' and not current_user.is_anonymous():
        if rec is None:
            rec = models.Pages()

        rec.save_from_form(request)
        return redirect(rec.data['url'])
    
    elif ( request.method == 'DELETE' and 
            not current_user.is_anonymous() and rec is not None ):
        rec.delete()
        return ""

    else:
        abort(401)
        
        
        
        
        
        
        
