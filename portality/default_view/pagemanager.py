
# this runs the Pagemanager endpoint for standard display of web pages

import json, time, requests, markdown, os

from flask import Blueprint, request, url_for, abort, make_response, flash
from flask import render_template, redirect
from flask.ext.login import current_user

import portality.util as util
from portality.core import app
import portality.models as models
from portality.view.forms import dropdowns


blueprint = Blueprint('Pagemanager', __name__)


if app.config.get('CONTENT_FOLDER',False):
    contentdir = os.path.dirname(os.path.abspath(__file__)).replace('/view','/templates/pagemanager/') + app.config['CONTENT_FOLDER']
    if not os.path.exists(contentdir):
        os.makedirs(contentdir)


# a method for editing the page
@blueprint.route('/<path:path>/edit', methods=['GET','POST'])
def edit(path='/'):
    if path != '/': path = '/' + path
    record = models.Pages.pull_by_url(path)

    if record is None:
        if current_user.is_anonymous():
            abort(404)
        else:
            return redirect('/' + path)
    elif current_user.is_anonymous() and not (rec.data.get('editable',False) and rec.data.get('accessible',False)):
        abort(401)
    else:
        if app.config.get('COLLABORATIVE',False):
            try:
                test = requests.get(app.config['COLLABORATIVE'])
                if test.status_code == 200:
                    padsavailable = True
                else:
                    padsavailable = False
            except:
                padsavailable = False
            
        # TODO: add a check - if index has more recent content than pad content, show a warning to sync the pad to index
        return render_template(
            'pagemanager/edit.html',
            padsavailable=padsavailable, 
            record=record
        )


# a method for managing page settings and creating / deleting pages
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
            _sync_delete(record)
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
                        _sync_delete(rec)
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

    url = '/' + path.lstrip('/').rstrip('/').replace('../',"")
    if url == '/': url = '/index'
    if url.endswith('.json'): url = url.replace('.json','')
    rec = models.Pages.pull_by_url(url)
    
    if rec is not None and rec.data.get('editable',False):
        return redirect(url_for('.edit',path=url))
    elif ( ( request.method == 'DELETE' or ( request.method == 'POST' and request.form['submit'] == 'Delete' ) ) and not current_user.is_anonymous() ):
        if rec is None:
            abort(404)
        else:
            _sync_delete(rec)
            return ""
    elif request.method == 'POST' and not current_user.is_anonymous():
        if rec is None: rec = models.Pages()
        rec.save_from_form(request)
        if app.config.get('CONTENT_FOLDER',False): _sync_fs_from_es(rec)
        return redirect(rec.data.get('url','/'))
    elif rec is None:
        if current_user.is_anonymous():
            abort(404)
        else:
            return redirect(url_for('.settings', path=url))
    elif request.method == 'GET':
        if current_user.is_anonymous() and not rec.data.get('accessible',True):
            abort(401)
        elif util.request_wants_json():
            resp = make_response( rec.json )
            resp.mimetype = "application/json"
            return resp
        else:
            try:
                content = render_template(
                    'pagemanager/content' + url,
                    record=rec
                )
            except:
                content = rec.data.get('content',"")

            content = markdown.markdown(content)

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

            # TODO: try adding js dynamic includes server-side?
            return render_template(
                'pagemanager/index.html',
                content=content,
                record=rec
            )

    else:
        abort(401)
        

# synchronise from EP to ES, then from ES to FS
@blueprint.route('/<path:path>/sync')
def sync(path=''):            

    url = '/' + path.lstrip('/').rstrip('/')
    if url == '/': url = '/index'
    if url.endswith('.json'): url = url.replace('.json','')
    rec = models.Pages.pull_by_url(url)

    if current_user.is_anonymous():
        abort(401)
    elif rec is None:
        abort(404)
    else:
        # save to ES
        if app.config.get('COLLABORATIVE',False):
            done1 = _sync_es_from_ep(rec)
            if done1:
                flash("Synchronised")
            else:
                flash("Error syncing")
            
        # save to FS
        if app.config.get('CONTENT_FOLDER',False):
            done2 = _sync_fs_from_es(rec)
            if done2:
                flash("Saved to disk")
            else:
                flash("Error saving to disk")                
            
        return redirect(url_for('.edit', path=path))


def _sync_es_from_ep(rec):
    try:
        a = app.config['COLLABORATIVE'].rstrip('/') + '/p/'
        a += rec.id + '/export/txt'
        c = requests.get(a)
        if rec.data.get('content',False) != c.text:
            rec.data['content'] = c.text
            rec.save()
        return True
    except:
        return False


def _sync_fs_from_es(rec):
    try:
        fn = contentdir + rec.data['url']
        sdir = os.path.dirname(fn)
        if not os.path.exists(sdir):
            os.makedirs(sdir)
        out = open(fn, 'w')
        out.write(rec.data['content'])
        out.close()
        return True
    except:
        return False


def _sync_ep_from_es(rec):
    try:
        target = app.config['COLLABORATIVE'] + '/api/1/setText?apikey='
        target += app.config['DELETE_REMOVES_EP'] + '&padID='
        target += str(record.id)
        target += '&text=' + rec.data["content"]
        requests.get(target)
        return True
    except:
        return False


def _sync_delete(rec):
    if app.config.get('DELETE_REMOVES_FS',False) and app.config.get('CONTENT_FOLDER',False):
        _sync_delete_fs(rec)
    if app.config.get('DELETE_REMOVES_EP',False) and app.config.get('COLLABORATIVE',False):
        _sync_delete_ep(rec)
    rec.delete()
    
def _sync_delete_fs(rec):
    fn = contentdir + rec.data['url']
    try:
        os.remove(fn)
        return True
    except:
        return False

def _sync_delete_ep(rec):
    try:
        target = app.config['COLLABORATIVE'] + '/api/1/deletePad?apikey='
        target += app.config['DELETE_REMOVES_EP'] + '&padID='
        target += str(record.id)
        requests.get(target)
        return True
    except:
        return False


'''

On page GET, update ES if FS last_modified is newer than last_updated
and also in this case push content to the EP if available

If page exists in ES on GET but not on FS, create it on FS. BUT need to check 
after git pull that if a page is deleted it should be removed from ES.
Also perhaps offer a config option to delete on FS instead of create in these
cases.

On page POST, if FS last_modified is newer than ES last_updated, reject
and trigger a normal sync

If page URL changes in POST, move file on FS to alternate location

have a specific function in "manage" to remove pages from FS and EP that are no 
longer present in ES


'''     
        
        
        
